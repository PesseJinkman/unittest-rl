def alternating_sum(nums):
    total = 0
    sign = 1
    for i, value in enumerate(nums):
        total += sign * value
        if i > 0:
            sign *= -1
    return total
