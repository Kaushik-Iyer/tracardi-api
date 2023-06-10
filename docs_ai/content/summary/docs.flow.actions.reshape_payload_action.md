This documentation describes how to use the Create Payload Action node in order to create data as payload output. It explains how to provide transformation configuration in order to create the payload, which includes using dot notation to access json properties from payload, profile, etc. It also provides an example of the configuration and the resulting object that will be returned. The configuration example includes mixing regular values with values read from profile, session, etc. The resulting object will include the properties specified in the configuration, such as the profile ID, data from the payload, and data from the event.