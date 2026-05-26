
def reciprocal_rank_fusion(idx_list1,idx_list2,k = 60):

    idx_score = {}
    for idx_l in [idx_list1,idx_list2]:
        for i,idx in enumerate(idx_l):
            if idx not in idx_score:
                idx_score[idx] = 1 / (i + k)
            else:
                idx_score[idx] += 1 / (i + k)
    
    result_idx = sorted(idx_score,key=idx_score.get,reverse=True)
    return result_idx