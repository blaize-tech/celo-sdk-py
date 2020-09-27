def upsert(sorted_list: list, change: dict):
    old_idx = None
    for ind, el in enumerate(sorted_list):
        if el['address'] == change['address']:
            old_idx = ind
            break
    
    if old_idx == None:
        raise Exception('')

    del sorted_list[old_idx]

    new_idx = None
    for ind, el in enumerate(sorted_list):
        if el['value'] < change['value']:
            new_idx = ind
            break
    
    if new_idx == None:
        sorted_list.append(change)
        return len(sorted_list) - 1
    else:
        sorted_list.insert(new_idx, change)
        return new_idx

def linked_list_change(sorted_list: list, change: dict):
    idx = upsert(sorted_list, change)
    greater = '0x0000000000000000000000000000000000000000' if idx == 0 else sorted_list[idx - 1]['address']
    lesser = '0x0000000000000000000000000000000000000000' if idx == len(sorted_list) - 1 else sorted_list[idx + 1]['address']

    return {'lesser': lesser, 'greater': greater}

def linked_list_changes(sorted_list: list, change_list: list):
    lessers = []
    greaters = []

    for it in change_list:
        res = linked_list_change(sorted_list, it)
        lessers.append(res['lesser'])
        greaters.append(res['greater'])
    
    return {'lessers': lessers, 'greaters': greaters, 'sorted_list': sorted_list}

def int_to_bytes(x: int) -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def string_to_bytes32(data):
    if len(data) > 32:
        myBytes32 = data[:32]
    else:
        myBytes32 = data.ljust(32, '0')
    return bytes(myBytes32, 'utf-8')
