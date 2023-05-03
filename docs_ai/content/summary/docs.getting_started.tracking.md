Customer tracking and identity resolution are techniques used to monitor the behavior of customers on a website or mobile app and to combine the data collected from different devices and sessions to create a complete profile of the customer. In Tracardi, a session is established when a user opens a browser or mobile app, and each click or event is recorded and sent to a server. The session ID is a unique identifier generated on the client side (e.g. web browser) and stored in cookies. It remains the same for the time the browser is opened. A new session ID is created only when the browser or app is closed and reopened.

On the other hand, the profile ID is a unique identifier for a user profile that is created when the user interacts with the website or app. It is generated by Tracardi, and it remains the same throughout the whole user's journey. It is stored in local storage of the browser. Each browser/device will have its own profile ID. Profile ID is attached to the browser and can be merged into single profile during identity resolution.

Identity resolution is the process of merging multiple profiles into a single profile. This is achieved by creating an identification point in Tracardi that checks if there are any profiles with the same merging key, eg. email address, telephone number, etc. It merges existing profiles generated through-out the customer journey into one profile. The resulting profile may have multiple profile IDs, which are used to identify different devices in order to have one profile data available to all devices.

The main differences between session ID and profile ID are that session IDs are unique identifiers generated on the client side (browser) when a user opens a browser or application, used to track a user's visit or session, stored in a cookie in the user's browser, and erased when the user closes the browser or app. On the other hand, profile IDs are unique identifiers for a user profile, generated by Tracardi when a user visits a website or application and their data is recorded, stored in browser local storage, and remain the same throughout the user's journey across multiple visits and devices. Profile IDs are also bound to the browser and are used as an identification point to merge different profiles and ensure a user's data is stored in a single profile across multiple devices.