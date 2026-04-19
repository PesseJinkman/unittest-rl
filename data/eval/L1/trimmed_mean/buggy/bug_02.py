def trimmed_mean(nums):
    if len(nums) < 3:
        return 0.0
    values = list(nums)
    values.remove(min(values))
    values.remove(max(values))
    return sum(values) / float(len(nums))
