import logging
import json
import azure.functions as func

# Power BI Workspace IDs to Exclude
excluded_workspaces = ["xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"]


def main(inEvent: func.EventHubEvent, outEvent: func.Out[bytes]):
    # Parse event payload to JSON
    payload = json.loads(inEvent.get_body().decode("utf-8"))

    # Exit on empty payload
    if (payload == {}):
        return  # Terminate

    # Ignore messages that aren't ENTITY_CREATE events
    op_type = str(payload['message']['operationType'])
    if (op_type != "ENTITY_CREATE"):
        return  # Terminate (not a create event)

    # Get specific elements from the payload
    logging.info('++++ New Purview Create Event Received ++++')
    entity_type = str(payload['message']['entity']['typeName'])
    guid = str(payload['message']['entity']['guid'])
    qualifiedName = str(payload['message']['entity']
                        ['attributes']['qualifiedName'])

    # Check the workspace exclusion list
    if (any(e in qualifiedName for e in excluded_workspaces)):
        logging.warn("Detected asset to be deleted: %s", qualifiedName)

        # Craft Delete Payload
        delete_by_guid = {
            "message": {
                "entities": [
                    {
                        "typeName": f"{entity_type}",
                        "uniqueAttributes": {
                            "qualifiedName": f"{qualifiedName}"
                        }
                    }
                ],
                "type": "ENTITY_DELETE_V2",
                "user": "<USER>"
            },
            "version": {
                "version": "1.0.0"
            }
        }

        # Write the DELETE event to the Kafka Event Hub
        logging.warn('Deleting: %s (GUID: %s)', entity_type, guid)
        outEvent.set(json.dumps(delete_by_guid))
