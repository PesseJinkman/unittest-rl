def sum_even_numbers(nums):
    total = 0
    for n in nums[:-1]:
        if n % 2 == 0:
            total += n
    return total
