def alternating_sum(nums):
    total = 0
    sign = 1
    for value in reversed(nums):
        total += sign * value
        sign *= -1
    return total
