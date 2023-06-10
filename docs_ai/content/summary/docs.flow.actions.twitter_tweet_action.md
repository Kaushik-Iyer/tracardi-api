This plugin allows users to post tweets to their Twitter feed. In order to use the plugin, users must have a Twitter account and generate access keys. There are four keys in total, and more information can be found in the Twitter resource documentation. The plugin takes any payload as input, and depending on the response, the plugin will trigger data on the response port if the response was successful, or on the error port if the response had an error.

The plugin also allows users to use a message template when creating a tweet. The template is a text file with special mark-up, and within double curly braces, users can place dot notation that reads data from the internal state of the workflow. For example, a template could be "Hello {{profile@pii.name}}". This would read the profile's name from the internal state of the workflow and include it in the tweet.