def merge_intervals(intervals):
    if not isinstance(intervals, list):
        raise TypeError('intervals must be a list')
    parsed = []
    for item in intervals:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise TypeError('each interval must be a 2-item list or tuple')
        start, end = item
        if not isinstance(start, int) or not isinstance(end, int):
            raise TypeError('interval bounds must be ints')
        if start > end:
            raise ValueError('interval start must be <= end')
        parsed.append([start, end])
    if not parsed:
        return []
    parsed.sort(key=lambda x: x[0])
    merged = [parsed[0][:]]
    for start, end in parsed[1:]:
        last = merged[-1]
        if start <= last[1]:
            if end > last[1]:
                last[1] = end
        else:
            merged.append([start, end])
    return merged
