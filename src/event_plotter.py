
import datetime
import logging
import time

import matplotlib
import matplotlib.pyplot as plt

from matplotlib.ticker import MaxNLocator

from config import COLOR_GRID, COLOR_BARS, COLOR_BARS_BORDERS, COLORS_TRAND_LINE

matplotlib.use('TkAgg')

logger = logging.getLogger(__name__)


def get_days_list_for_n_days_till_tomorrow(days):
    start_date = datetime.date.today() - datetime.timedelta(days=days)
    end_date = datetime.date.today()
    out = []
    day_count = (end_date - start_date).days + 1  # for today
    for single_date in [d for d in (start_date + datetime.timedelta(n) for n in range(day_count)) if d <= end_date]:
        logger.critical(time.strftime('%Y-%m-%d', single_date.timetuple()))
        out.append(time.strftime('%Y-%m-%d', single_date.timetuple()))
    return out


def get_hours_list_for_n_days_till_tomorrow(days):

    def hour_range(start, end):
        while start < end:
            yield start
            start += datetime.timedelta(hours=1)

    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    end_date = datetime.datetime.now() + datetime.timedelta(hours=1)  # with current hour
    logger.warning('start: %s' % start_date)
    logger.warning('end: %s' % end_date)
    out = [h.strftime('%d-%m %H') for h in hour_range(start_date, end_date)]
    logger.warning('OUT: %s' % str(out))
    return out


def plot_day_events(cat_name, events_list):
    
    # PLOT
    fig, ax = plt.subplots()
    plt.grid(axis='x', color=COLOR_GRID, linestyle='--', linewidth=0.1)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
    ax.set_axisbelow(True)  # hide grid behind bars
    hours = get_hours_list_for_n_days_till_tomorrow(1)
    bar_labels = hours

    logger.critical(len(hours))
    logger.critical(str(hours))
    logger.critical('Event list: %s' % str(events_list))

    amounts = []
    for exact_hour in hours:
        logger.critical('Event hour: %s\n' % str(exact_hour))
        hour_data = []
        for event in events_list:
            logger.warning('E: %s' % str(event.created_at.strftime('%d-%m %H')))
            if str(exact_hour) == str(event.created_at.strftime('%d-%m %H')):
                hour_data.append(event.amount)
            else:
                logger.info('%s not equals %s\n' % (str(exact_hour), str(event.created_at.strftime('%d-%m %H'))))
        amounts.append(hour_data)

    logger.warning('amounts: %s\n' % str(amounts))

    total_amounts = [sum(day_value) for day_value in amounts]
    logger.warning('total_amounts: %s\n' % str(total_amounts))
    
    for bar in range(len(amounts)):
        logger.warning(str(amounts[bar]))
        if amounts[bar]:
            left = 0
            for value in amounts[bar]:
                logger.warning('num of bar: %s\n' % str(bar))
                logger.warning('value: %s\n' % str(value))
                logger.warning('left: %s\n' % str(left))
                plt.barh(y=bar, width=value, left=left,
                         color=COLOR_BARS, edgecolor=COLOR_BARS_BORDERS, height=0.6)
                left += value
        else:
            pass

    ax.set_yticks(range(len(bar_labels)), bar_labels, size='small')

    plt.subplots_adjust(bottom=0.2)
    plt.suptitle(t='Total day amount for %s : %s' % (cat_name, str(sum(total_amounts))),
                 x=0.65)
    result = plt.savefig('temp.png')
    logger.warning('save result: %s\n' % str(result))
    plt.close()


def plot_week_events(cat_name, events_list):

    # PLOT
    fig, ax = plt.subplots()
    plt.grid(axis='y', color=COLOR_GRID, linestyle='--', linewidth=0.1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
    ax.set_axisbelow(True)  # hide grid behind bars
    days = get_days_list_for_n_days_till_tomorrow(7)
    bar_labels = days

    amounts = []
    for day_date in days:
        logger.critical('day date: %s\n' % str(day_date))
        day_data = []
        for event in events_list:
            if day_date in str(event.created_at):
                day_data.append(event.amount)
        amounts.append(day_data)

    logger.warning('amounts: %s\n' % str(amounts))

    total_amounts = [sum(day_value) for day_value in amounts]
    logger.warning('total_amounts: %s\n' % str(total_amounts))
    logger.warning('amounts: %s\n' % str(amounts))

    for bar in range(len(amounts)):
        logger.warning(str(amounts[bar]))
        if amounts[bar]:
            bottom = 0
            for value in amounts[bar]:
                logger.warning('num of bar: %s\n' % str(bar))
                logger.warning('value: %s\n' % str(value))
                logger.warning('bottom: %s\n' % str(bottom))
                plt.bar(x=bar, height=value, bottom=bottom,
                        color=COLOR_BARS, edgecolor=COLOR_BARS_BORDERS, width=0.15)
                bottom += value
        else:
            pass

    ax.plot(total_amounts, color=COLORS_TRAND_LINE)
    ax.set_xticks(range(len(bar_labels)), bar_labels, size='small', rotation='vertical')

    plt.subplots_adjust(bottom=0.2)
    plt.suptitle(t='Total week amount for %s : %s' % (cat_name, str(sum(total_amounts))),
                 x=0.65)
    result = plt.savefig('temp.png')
    logger.warning('save result: %s\n' % str(result))
    plt.close()


def plot_month_events(cat_name, events_list):

    # PLOT
    fig, ax = plt.subplots()
    plt.grid(axis='y', color=COLOR_GRID, linestyle='--', linewidth=0.1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
    ax.set_axisbelow(True)  # hide grid behind bars
    days = get_days_list_for_n_days_till_tomorrow(31)
    bar_labels = days

    amounts = []
    for day_date in days:
        logger.critical('day date: %s\n' % str(day_date))
        day_data = []
        for event in events_list:
            if day_date in str(event.created_at):
                day_data.append(event.amount)
        amounts.append(day_data)

    logger.warning('amounts: %s\n' % str(amounts))

    total_amounts = [sum(day_value) for day_value in amounts]
    logger.warning('total_amounts: %s\n' % str(total_amounts))
    logger.warning('amounts: %s\n' % str(amounts))

    for bar in range(len(amounts)):
        logger.warning(str(amounts[bar]))
        if amounts[bar]:
            bottom = 0
            for value in amounts[bar]:
                plt.bar(x=bar, height=value, bottom=bottom,
                        color=COLOR_BARS, edgecolor=COLOR_BARS_BORDERS, width=0.5)
                bottom += value
        else:
            pass

    ax.plot(total_amounts, color=COLORS_TRAND_LINE)
    ax.set_xticks(range(len(bar_labels)), bar_labels, size='small', rotation='vertical')

    plt.subplots_adjust(bottom=0.2)
    plt.suptitle(t='Total week amount for %s : %s' % (cat_name, str(sum(total_amounts))),
                 x=0.65)
    result = plt.savefig('temp.png')
    logger.warning('save result: %s\n' % str(result))
    plt.close()
