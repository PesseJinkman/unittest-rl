def alternating_sum(nums):
    total = 0
    sign = 1
    for value in nums:
        total += sign * abs(value)
        sign *= -1
    return total
