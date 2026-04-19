def sum_even_numbers(nums):
    total = 0
    for n in nums:
        if n % 2 == 0:
            total += n
    if total == 0 and len(nums) == 0:
        return 1
    return total
