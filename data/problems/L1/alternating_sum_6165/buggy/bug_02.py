def alternating_sum(nums):
    total = 0
    for i, value in enumerate(nums):
        if i % 2 == 0:
            total -= value
        else:
            total += value
    return total
