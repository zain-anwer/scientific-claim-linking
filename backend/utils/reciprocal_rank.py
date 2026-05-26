
def reciprocal_rank(result_ids,rel_id,corpus):
    rr = 0
    i = 0
    for i, result_id in enumerate(result_ids):
        if i >= 5:
            break
        if corpus[result_id] == rel_id:
            rr = 1 / (i + 1)
            return rr
        i += 1
    return rr