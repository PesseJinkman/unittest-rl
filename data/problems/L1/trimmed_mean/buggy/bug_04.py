def trimmed_mean(nums):
    if len(nums) < 3:
        return 0.0
    values = sorted(nums)
    values = values[2:]
    return sum(values) / float(len(values))
