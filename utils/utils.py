
def str_to_dict(str_data):
    result = str_data.split()
    temp = []
    for p in result:
        temp.append(p.split('='))
    result = dict(temp)
    return result