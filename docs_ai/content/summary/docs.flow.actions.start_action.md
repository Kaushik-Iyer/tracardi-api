This plugin is used to start every workflow. It has two configuration options, one for production runs and one for debug runs. For production runs, the user can set if they want to collect debugging information and what event types should trigger the start of the workflow. For debug runs, the user can enable profile-less and session-less events, manually specify event properties, use a particular event ID, or use a real event type instead of an auto-generated one. The plugin also includes a JSON configuration object that contains the debug boolean, an array of event types, booleans for profile-less and session-less events, a serialized JSON for properties, an event ID, and an event type object.