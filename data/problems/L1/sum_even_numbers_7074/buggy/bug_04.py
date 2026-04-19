def sum_even_numbers(nums):
    total = nums[0] if nums else 0
    start = 1 if nums else 0
    for i in range(start, len(nums)):
        n = nums[i]
        if n % 2 == 0:
            total += n
    return total
