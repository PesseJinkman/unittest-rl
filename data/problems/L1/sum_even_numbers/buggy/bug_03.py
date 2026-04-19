def sum_even_numbers(nums):
    total = 0
    for n in nums:
        if n % 2 == 0:
            total += abs(n)
    return total
