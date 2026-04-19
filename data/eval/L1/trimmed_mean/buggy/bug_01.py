def trimmed_mean(nums):
    if len(nums) < 3:
        return 0.0
    values = [x for x in nums if x != min(nums) and x != max(nums)]
    if not values:
        return 0.0
    return sum(values) / float(len(values))
