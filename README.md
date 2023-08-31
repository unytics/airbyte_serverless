# Simple Airbyte

    except:
        raise Exception('Could not parse message: ' + )
    if (message['type'] == 'LOG') and print_log:
        print(message.log.json(exclude_unset=True))
    elif message['type'] == 'TRACE':
        raise Exception(message['trace']['error.message'])
    else:
        yield message