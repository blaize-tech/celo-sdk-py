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

if __name__ == "__main__":
    # lst = [
    #     { 'address': 'address 1', 'value': 7 },
    #     { 'address': 'address 2', 'value': 5 },
    #     { 'address': 'address 3', 'value': 4 },
    #     { 'address': 'address 4', 'value': 3 },
    #     { 'address': 'address 5', 'value': 2 },
    #     { 'address': 'address 6', 'value': 2 },
    #     { 'address': 'address 7', 'value': 1 },
    # ]
    # changes = [{'address': 'address 3', 'value': 2}]
    # expected = {
    #     greaters: ['address 6'],
    #     lessers: ['address 7'],
    #   }

    lst = [
        { 'address': 'address 1', 'value': 7 },
        { 'address': 'address 2', 'value': 5 },
        { 'address': 'address 3', 'value': 4 },
        { 'address': 'address 4', 'value': 3 },
        { 'address': 'address 5', 'value': 2 },
        { 'address': 'address 6', 'value': 2 },
        { 'address': 'address 7', 'value': 1 },
    ]
    changes = [{'address': 'address 3', 'value': 2}, {'address': 'address 2', 'value': 0}]
    #expected = {
    #     greaters: ['address 6', 'address 7'],
    #     lessers: ['address 7', NULL_ADDRESS],
    #   }

    print(linked_list_changes(lst, changes))