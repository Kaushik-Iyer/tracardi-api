from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response
from tracardi.domain.enum.production_draft import ProductionDraft
from tracardi.domain.event_metadata import EventMetadata
from tracardi.domain.metadata import ProfileMetadata
from tracardi.domain.time import EventTime, ProfileTime
from tracardi.exceptions.exception import StorageException
from tracardi.domain.console import Console
from tracardi.service.console_log import ConsoleLog
from tracardi.service.secrets import encrypt
from tracardi.service.storage.driver import storage
from tracardi.service.utils.getters import get_entity_id
from tracardi.service.wf.domain.flow_history import FlowHistory
from tracardi.service.wf.domain.work_flow import WorkFlow
from tracardi.domain.flow_meta_data import FlowMetaData
from tracardi.domain.entity import Entity
from tracardi.domain.event import Event, EventSession
from tracardi.domain.flow import Flow
from tracardi.service.wf.domain.flow import Flow as GraphFlow
from tracardi.domain.flow import FlowRecord
from tracardi.domain.profile import Profile
from tracardi.domain.session import Session, SessionMetadata, SessionTime
from tracardi.domain.resource import Resource
from tracardi.domain.value_object.bulk_insert_result import BulkInsertResult
from .auth.permissions import Permissions
from ..config import server

router = APIRouter(
    dependencies=[Depends(Permissions(roles=["admin", "developer"]))]
)


async def _load_record(id: str) -> Optional[FlowRecord]:
    return FlowRecord.create(await storage.driver.flow.load_by_id(id))


async def _store_record(data: Entity):
    return await storage.driver.flow.save(data)


@router.get("/flows/refresh", tags=["flow"], include_in_schema=server.expose_gui_api)
async def flow_refresh():
    return await storage.driver.flow.refresh()


@router.post("/flow/draft/nodes/rearrange", tags=["flow"], response_model=dict, include_in_schema=server.expose_gui_api)
async def rearrange_flow(flow: Flow):
    """
    Rearranges the send workflow nodes.
    """

    # Frontend edge-id is long. Save space and md5 it.

    if flow.flowGraph is not None:
        flow.flowGraph.shorten_edge_ids()

    flow.arrange_nodes()

    return flow


@router.post("/flow/draft", tags=["flow"], response_model=BulkInsertResult, include_in_schema=server.expose_gui_api)
async def upsert_flow_draft(draft: Flow, rearrange_nodes: Optional[bool] = False):
    """
    Creates draft of workflow. If there is production version of the workflow it stays intact.
    """
    # Frontend edge-id is long. Save space and md5 it.

    if draft.flowGraph is not None:
        draft.flowGraph.shorten_edge_ids()

    if rearrange_nodes is True:
        draft.arrange_nodes()

        # Check if origin flow exists

    flow_record = await storage.driver.flow.load_record(draft.id)  # type: FlowRecord

    if flow_record is None:
        flow_record = draft.get_empty_workflow_record(draft.type)

    flow_record.draft = encrypt(draft.dict())

    return await storage.driver.flow.save_record(flow_record)


@router.get("/flow/draft/{id}", tags=["flow"], response_model=Optional[Flow], include_in_schema=server.expose_gui_api)
async def load_flow_draft(id: str, response: Response):
    """
    Loads draft version of flow with given ID (str)
    """

    flow_record = await storage.driver.flow.load_record(id)  # type: FlowRecord

    if flow_record is None:
        response.status_code = 404
        return None

    # Return draft if exists
    if flow_record.draft:
        return flow_record.get_draft_workflow()

        # Fallback to production version
    if flow_record.production:
        return flow_record.get_production_workflow()

    return flow_record.get_empty_workflow(id)


@router.get("/flow/production/{id}", tags=["flow"], response_model=Optional[Flow],
            include_in_schema=server.expose_gui_api)
async def get_flow(id: str, response: Response):
    """
    Returns production version of flow with given ID (str)
    """
    flow_record = await storage.driver.flow.load_record(id)  # type: FlowRecord

    if flow_record is None:
        response.status_code = 404
        return None

    if flow_record.production:
        return flow_record.get_production_workflow()

    return flow_record.get_empty_workflow(id)


@router.get("/flow/{production_draft}/{id}/restore", tags=["flow"], response_model=Flow,
            include_in_schema=server.expose_gui_api)
async def restore_production_flow_backup(id: str, production_draft: ProductionDraft):
    """
    Returns previous version of production flow with given ID (str)
    """
    flow_record = await storage.driver.flow.load_record(id)  # type: FlowRecord

    if flow_record is None:
        raise HTTPException(status_code=404, detail="Flow id: `{}` does not exist.".format(id))

    try:
        if production_draft.value == ProductionDraft.production:
            flow_record.restore_production_from_backup()
        else:
            flow_record.restore_draft_from_production()
    except ValueError as e:
        raise HTTPException(status_code=406, detail=str(e))

    result = await storage.driver.flow.save_record(flow_record)
    if result.saved == 1:
        if production_draft.value == ProductionDraft.production:
            return flow_record.get_production_workflow()
        return flow_record.get_draft_workflow()


@router.post("/flow/production", tags=["flow"], response_model=BulkInsertResult,
             include_in_schema=server.expose_gui_api)
async def upsert_flow(flow: Flow):
    """
        Creates production version of workflow. If there is a draft version of the workflow it is overwritten
        by the production version. This may be the subject to change.
    """
    old_flow_record = await storage.driver.flow.load_record(flow.id)
    flow_record = flow.get_production_workflow_record()
    if flow_record is None or old_flow_record is None:
        raise HTTPException(status_code=406, detail="Can not deploy missing draft workflow")
    flow_record.backup = old_flow_record.production
    flow_record.deployed = True
    return await _store_record(flow_record)


@router.get("/flow/metadata/{id}", tags=["flow"], response_model=FlowRecord, include_in_schema=server.expose_gui_api)
async def get_flow_details(id: str):
    """
    Returns flow metadata of flow with given ID (str)
    """
    flow_record = await _load_record(id)

    if flow_record is None:
        raise HTTPException(status_code=404, detail="Missing flow record {}".format(id))

    return flow_record


@router.post("/flow/metadata", tags=["flow"], response_model=BulkInsertResult, include_in_schema=server.expose_gui_api)
async def upsert_flow_details(flow_metadata: FlowMetaData):
    """
    Adds new flow metadata for flow with given id (str)
    """
    flow_record = await _load_record(flow_metadata.id)
    if flow_record is None:

        # create new

        flow_record = FlowRecord(**flow_metadata.dict())
        flow_record.draft = encrypt(Flow(
            id=flow_metadata.id,
            name=flow_metadata.name,
            description=flow_metadata.description,
            type=flow_metadata.type
        ).dict())
        flow_record.production = encrypt(Flow(
            id=flow_metadata.id,
            name=flow_metadata.name,
            description=flow_metadata.description,
            type=flow_metadata.type
        ).dict())

    else:

        # update

        draft_flow = flow_record.get_draft_workflow()
        draft_flow.name = flow_metadata.name
        flow_record.draft = encrypt(draft_flow.dict())

        flow_record.name = flow_metadata.name
        flow_record.description = flow_metadata.description
        flow_record.projects = flow_metadata.projects
        flow_record.type = flow_metadata.type

    return await _store_record(flow_record)


@router.post("/flow/draft/metadata", tags=["flow"], response_model=BulkInsertResult,
             include_in_schema=server.expose_gui_api)
async def upsert_flow_details(flow_metadata: FlowMetaData):
    """
    Adds new draft metadata to flow with defined ID (str)
    """

    flow_record = await _load_record(flow_metadata.id)

    if flow_record is None:
        raise HTTPException(status_code=404, detail="Flow `{}` does not exist.".format(flow_metadata.id))

    flow_record.name = flow_metadata.name
    flow_record.description = flow_metadata.description
    flow_record.projects = flow_metadata.projects
    flow_record.type = flow_metadata.type

    if flow_record.draft:
        draft_workflow = flow_record.get_draft_workflow()

        draft_workflow.name = flow_metadata.name
        draft_workflow.description = flow_metadata.description
        draft_workflow.projects = flow_metadata.projects
        draft_workflow.type = flow_metadata.type

        flow_record.draft = encrypt(draft_workflow.dict())

    result = await _store_record(flow_record)
    await storage.driver.flow.refresh()
    return result


@router.get("/flow/{id}/lock/{lock}", tags=["flow"],
            response_model=BulkInsertResult,
            include_in_schema=server.expose_gui_api)
async def update_flow_lock(id: str, lock: str):
    flow_record = await _load_record(id)

    if flow_record is None:
        raise HTTPException(status_code=406, detail="Flow `{}` does not exist.".format(id))

    flow_record.set_lock(True if lock.lower() == 'yes' else False)
    return await _store_record(flow_record)


@router.post("/flow/debug", tags=["flow"],
             include_in_schema=server.expose_gui_api)
async def debug_flow(flow: GraphFlow):
    """
        Debugs flow sent in request body
    """
    profile = Profile(id="@debug-profile-id",
                      metadata=ProfileMetadata(
                          time=ProfileTime(
                              insert=datetime.utcnow()
                          )
                      ))
    session = Session(id="@debug-session-id",
                      metadata=SessionMetadata(
                          time=SessionTime(
                              insert=datetime.utcnow(),
                              timestamp=datetime.timestamp(datetime.utcnow())
                          )
                      ))
    event_session = EventSession(
        id=session.id,
        start=session.metadata.time.insert,
        duration=session.metadata.time.duration
    )
    session.operation.new = True

    event = Event(
        metadata=EventMetadata(time=EventTime(insert=datetime.utcnow())),
        id='@debug-event-id',
        type="@debug-event-type",
        source=Resource(id="@debug-source-id", type="web-page"),
        session=event_session,
        profile=profile,
        context={}
    )

    workflow = WorkFlow(
        FlowHistory(history=[])
    )

    ux = []

    flow_invoke_result = await workflow.invoke(flow, event, profile, session, ux, debug=True)

    console_log = ConsoleLog()
    profile_save_result = None
    try:
        # Store logs in one console log
        for log in flow_invoke_result.log_list:
            console = Console(
                origin="node",
                event_id=get_entity_id(flow_invoke_result.event),
                flow_id=flow.id,
                profile_id=get_entity_id(flow_invoke_result.profile),
                node_id=log.node_id,
                module=log.module,
                class_name=log.class_name,
                type=log.type,
                message=log.message,
                traceback=log.traceback
            )
            console_log.append(console)

    except StorageException as e:
        console = Console(
            origin="profile",
            event_id=get_entity_id(flow_invoke_result.event),
            flow_id=flow.id,
            module='tracardi_api.flow_endpoint',
            class_name='log.class_name',
            type='debug_flow',
            message=str(e)
        )
        console_log.append(console)

    return {
        'logs': [log.dict() for log in console_log],
        "debugInfo": flow_invoke_result.debug_info.dict(),
        "update": profile_save_result,
        "ux": ux
    }


@router.delete("/flow/{id}", tags=["flow"], response_model=Optional[dict], include_in_schema=server.expose_gui_api)
async def delete_flow(id: str, response: Response):
    """
    Deletes flow with given id (str)
    """
    # Delete rule before flow
    rule_delete_result = await storage.driver.rule.delete_by_id(id)
    flow_delete_result = await storage.driver.flow.delete_by_id(id)

    if flow_delete_result is None:
        response.status_code = 404
        return None

    await storage.driver.flow.refresh()

    return {
        "rule": rule_delete_result,
        "flow": flow_delete_result
    }
