from library.config.mqtt import Topic


def fix_mqtt_topic_subscribe_name(topic: Topic) -> str:
    """
    Can't publish to topic names with wildcards
    @param topic: the MQTT Topic to normalize
    @type topic: Topic
    @return: topic name without wildcards
    @rtype: str
    """
    return topic.name.replace("#", "anything")
