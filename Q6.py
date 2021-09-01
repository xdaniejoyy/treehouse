from datetime import datetime
import re


def count_date(file_name):

    text = []
    with open(file_name, 'r') as file:
        for line in file:
            text.append(line)

    counter = 0
    pattern = re.compile(
        "(0[1-9]|[1-2][0-9]|3[0-1])\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept|Oct|Nov|Dec)\s+([0-9]{4})")

    for line in text:
        for group in line.split():
            # Use strptime to avoid out-of-range date formats
            try:
                datetime.strptime(group, '%Y/%m/%d')
                counter += 1
            except:
                try:
                    datetime.strptime(group, '%m/%d/%Y')
                    counter += 1
                except:
                    try:
                        datetime.strptime(group, '%d/%m/%Y')
                        counter += 1
                    except:
                        continue
        counter += len(re.findall(pattern, line))

    return counter


print(count_date('data/sample_q6.txt'))