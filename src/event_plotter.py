from random import choice
import datetime
import logging
import time

import matplotlib
import matplotlib.pyplot as plt

import numpy as np
import pylab as pl

from matplotlib.ticker import MaxNLocator

from config import COLOR_GRID, COLOR_BARS, COLOR_BARS_BORDERS, COLORS_TRAND_LINE

from models import Events

matplotlib.use('Agg')

logger = logging.getLogger(__name__)


def get_days_list_for_n_days_till_tomorrow(days):
    start_date = datetime.date.today() - datetime.timedelta(days=days)
    end_date = datetime.date.today()
    out = []
    day_count = (end_date - start_date).days + 1  # for today
    for single_date in [d for d in (start_date + datetime.timedelta(n) for n in range(day_count)) if d <= end_date]:
        out.append({'value': time.strftime('%Y-%m-%d', single_date.timetuple()),
                    'is_weekend': True if single_date.weekday() >= 5 else False})
    return out


def get_hours_list_for_n_days_till_tomorrow(days):

    def hour_range(start, end):
        while start < end:
            yield start
            start += datetime.timedelta(hours=1)

    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    end_date = datetime.datetime.now() + datetime.timedelta(hours=1)  # with current hour
    out = [h.strftime('%d-%m %H') for h in hour_range(start_date, end_date)]
    return out


def plot_day_events(user_db_id, cat_name, events_list):
    
    # PLOT
    fig, ax = plt.subplots()
    plt.grid(axis='x', color=COLOR_GRID, linestyle='--', linewidth=0.1)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
    ax.set_axisbelow(True)  # hide grid behind bars
    hours = get_hours_list_for_n_days_till_tomorrow(1)
    bar_labels = hours

    amounts = []
    for exact_hour in hours:
        hour_data = []
        for event in events_list:
            if str(exact_hour) == str(event.created_at.strftime('%d-%m %H')):
                hour_data.append(event.amount)
            else:
                logger.info('%s not equals %s\n' % (str(exact_hour), str(event.created_at.strftime('%d-%m %H'))))
        amounts.append(hour_data)

    total_amounts = [sum(day_value) for day_value in amounts]
    
    for bar in range(len(amounts)):
        if amounts[bar]:
            left = 0
            for value in amounts[bar]:
                plt.barh(y=bar, width=value, left=left,
                         color=COLOR_BARS, edgecolor=COLOR_BARS_BORDERS, height=0.6)
                left += value
        else:
            pass

    ax.set_yticks(range(len(bar_labels)), bar_labels, size='small')

    plt.subplots_adjust(bottom=0.2)
    plt.suptitle(t='Total day amount for %s : %s' % (cat_name, str(sum(total_amounts))),
                 x=0.65)
    plt.savefig('temp_%s.png' % user_db_id)
    plt.close()


def plot_week_events(user_db_id, cat_name, events_list):

    # PLOT
    fig, ax = plt.subplots()
    plt.grid(axis='y', color=COLOR_GRID, linestyle='--', linewidth=0.1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
    ax.set_axisbelow(True)  # hide grid behind bars
    days = get_days_list_for_n_days_till_tomorrow(7)
    bar_labels = days

    amounts = []
    for day_date in days:
        day_data = []
        for event in events_list:
            if day_date.get('value') in str(event.created_at):
                day_data.append(event.amount)
        amounts.append(day_data)

    total_amounts = [sum(day_value) for day_value in amounts]

    for bar in range(len(amounts)):
        if amounts[bar]:
            bottom = 0
            for value in amounts[bar]:
                plt.bar(x=bar, height=value, bottom=bottom,
                        color=COLOR_BARS, edgecolor=COLOR_BARS_BORDERS, width=0.15)
                bottom += value
        else:
            pass

    ax.plot(total_amounts, color=COLORS_TRAND_LINE)
    ax.set_xticks(range(len(bar_labels)), [bar.get('value') for bar in bar_labels], size='small', rotation='vertical')
    # update weekends with bold
    for i in range(len(bar_labels)):
        if bar_labels[i].get('is_weekend'):
            ax.get_xticklabels()[i].set_weight('bold')

    plt.subplots_adjust(bottom=0.2)
    plt.suptitle(t='Total week amount for %s : %s' % (cat_name, str(sum(total_amounts))),
                 x=0.65)
    plt.savefig('temp_%s.png' % user_db_id)
    plt.close()


def plot_week_events_custom(user_db_id, cat_name, events_list, **kwargs):

    if cat_name == 'WEIGHT':
        CustomCatPlotter().plot_weight(user_db_id=user_db_id, cat_name=cat_name, events_list=events_list,
                                       period_days=7, **kwargs)

    else:
        logger.debug(f'Custom function for {cat_name} no exists!')
        plot_week_events(user_db_id, cat_name, events_list)


def plot_month_events(user_db_id, cat_name, events_list):

    # PLOT
    fig, ax = plt.subplots()
    plt.grid(axis='y', color=COLOR_GRID, linestyle='--', linewidth=0.1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
    ax.set_axisbelow(True)  # hide grid behind bars
    days = get_days_list_for_n_days_till_tomorrow(31)
    bar_labels = days

    amounts = []
    for day_date in days:
        day_data = []
        for event in events_list:
            if day_date.get('value') in str(event.created_at):
                day_data.append(event.amount)
        amounts.append(day_data)

    total_amounts = [sum(day_value) for day_value in amounts]

    for bar in range(len(amounts)):
        if amounts[bar]:
            bottom = 0
            for value in amounts[bar]:
                plt.bar(x=bar, height=value, bottom=bottom,
                        color=COLOR_BARS, edgecolor=COLOR_BARS_BORDERS, width=0.5)
                bottom += value
        else:
            pass

    ax.plot(total_amounts, color=COLORS_TRAND_LINE)
    ax.set_xticks(range(len(bar_labels)), [bar.get('value') for bar in bar_labels], size='small', rotation='vertical')
    # update weekends with bold
    for i in range(len(bar_labels)):
        if bar_labels[i].get('is_weekend'):
            ax.get_xticklabels()[i].set_weight('bold')

    plt.subplots_adjust(bottom=0.2)
    plt.suptitle(t='Total week amount for %s : %s' % (cat_name, str(sum(total_amounts))),
                 x=0.65)
    plt.savefig('temp_%s.png' % user_db_id)
    plt.close()


def plot_month_events_custom(user_db_id, cat_name, events_list, **kwargs):

    if cat_name == 'WEIGHT':
        CustomCatPlotter().plot_weight(user_db_id=user_db_id, cat_name=cat_name, events_list=events_list,
                                       period_days=31, **kwargs)


class CustomCatPlotter:

    def plot_weight(self, user_db_id, cat_name, events_list, period_days, **kwargs):

        logger.warning('events_list: %s\n' % str(events_list))
        logger.warning('events_list len: %s\n' % len(events_list))

        # PLOT WEIGHT
        fig, ax = plt.subplots()
        ax.grid(b=True, axis='x', color='black', linestyle='-', linewidth=0.1)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # integer Y axe
        # ax.set_axisbelow(True)  # hide grid behind bars

        days = get_days_list_for_n_days_till_tomorrow(period_days)
        bar_labels = days

        logger.warning('days: %s\n' % str(days))

        # get start value for plot
        if events_list[0]:
            last_previous_value = events_list[0].amount
        else:
            last_previous_value = Events.select() \
                .where((Events.user_id == user_db_id) &
                       (Events.creted_at < datetime.date.today() - datetime.timedelta(days=period_days))) \
                .order_by(Events.id.desc()).get().amount

        logger.warning('last_previous_value: %s\n' % str(last_previous_value))

        if events_list[0] is False:
            events_list[0] = last_previous_value

        # make values list for plotting
        amounts = []
        current_value = last_previous_value
        for i in range(len(days)):
            logger.critical('day date: %s\n' % str(days[i]))
            for event in events_list:
                if days[i].get('value') in str(event.created_at):
                    current_value = event.amount
            amounts.append(current_value)

        # get and plot average amount
        avg_weight = float(sum(amounts)) / int(len([b for b in amounts if b]))
        ax.axline((0, avg_weight), (1, avg_weight), linewidth=0.7, color="skyblue")
        # set average title
        if sum(amounts[:int(len(amounts)/3)])/int(len(amounts)/3) > avg_weight:
            title_height = avg_weight - 0.1
        else:
            title_height = avg_weight + 0.05
        logger.warning('TH: %s' % title_height)
        plt.text(0.2, title_height, 'average = %s' % str(avg_weight)[:5], rotation=360, color="skyblue", fontsize=8),
                 # weight='bold')

        # plot line with styling
        for i in range(1, len(amounts)):
            if amounts[i] == amounts[i-1]:
                ax.plot(np.linspace(i-1, i, 2), amounts[i-1:i+1],
                        color='firebrick', linestyle='--')
            else:
                ax.plot(np.linspace(i-1, i, 2), amounts[i-1:i + 1],
                        color='firebrick', linestyle='-', marker='o')

        logger.warning('amounts: %s\n' % str(amounts))


        # set dates as x ticks
        ax.set_xticks(range(len(bar_labels)), [bar.get('value') for bar in bar_labels],
                      fontsize=7, rotation='vertical')
        # update weekends with bold
        for i in range(len(bar_labels)):
            if bar_labels[i].get('is_weekend'):
                ax.get_xticklabels()[i].set_weight('bold')

        # set y ticks
        # y_ticks = [int(avg_weight-i) for i in [-2, -1, 0, 1, 2]]
        mi, ma = min(amounts), max(amounts)
        logger.warning('Minmax: %s, %s' % (mi, ma))
        y_ticks = [int(mi), int(avg_weight), int(ma), int(ma+1)]
        ax.set_yticks(y_ticks, minore=True)

        # set values on line
        line = ax.lines[0]
        logger.warning('Y data: %s' % str(line.get_ydata()))

        for i in range(len(amounts)):
            y_value = amounts[i] if amounts[i] != amounts[i-1] else None
            x_value = i

            if y_value:
                label = "{:.2f}".format(y_value)
                # set left padding for right side plot labels
                x_padding = 20 if i < len(amounts) / 2 else -20
                # set bottom padding for right side plot labels
                y_padding = 3 if i < len(amounts) / 2 else -3
                # ax.annotate(label, (x_value, y_value), xytext=(x_padding, y_padding),
                #             textcoords="offset points", ha='center', va='bottom',
                #             color="slategray", weight='bold')

                # if y_value > avg_weight:
                # (x_padding, y_padding) = (10, 30) if y_value > avg_weight else (-10, -30)
                # x_padding = 10 if i < len(amounts) / 2 else -10
                x_padding = choice([40, 30, 20]) if i < len(amounts) / 2 else choice([-40, -30, -20])
                # y_padding = 30 if y_value > avg_weight else -30
                # y_padding = choice([30, 20]) if not i & 1 else choice([-30, -20])
                y_padding = choice([30, 20, -30]) if not i & 1 else choice([-30, -20, 30])
                y_padding = choice([18, 30, 47]) if amounts[i] >= amounts[i-1] else choice([-18, -30, -47])

                if y_value == mi:
                    y_padding = -30
                    x_padding = -20
                if y_value == ma:
                    y_padding = 20
                    x_padding = 20

                # set first and last annotations paddings
                if i == 0:  # first value in list
                    x_padding = 20
                try:
                    _ = amounts[i+1]
                except IndexError:  # last value in list
                    x_padding = -20

                logger.warning('!: %s - %s' % (i, x_padding))
                # logger.warning('?: %s' % (not amounts[i+1]))

                ax.annotate(label, (x_value, y_value),
                            xytext=(x_padding, y_padding),
                            bbox=dict(boxstyle="round", fc="none", ec="lightgray"),
                            size=8,
                            xycoords='data',
                            # xytext=(10, -40),
                            textcoords='offset points', ha='center',
                            arrowprops=dict(
                                arrowstyle="fancy",
                                fc="none", ec="lightgray",
                                connectionstyle="angle3,angleA=0,angleB=-90"), alpha=0.7)
                        # arrowprops=dict(arrowstyle="->",
                        #     connectionstyle="angle,angleA=0,angleB=80,rad=20",
                        #                 fc="0.6", ec="none"))

        #         ax.annotate("Independence Day", xy=('2012-7-4', 4250),  xycoords='data',
        #             bbox=dict(boxstyle="round", fc="none", ec="gray"),
        #             xytext=(10, -40), textcoords='offset points', ha='center',
        #             arrowprops=dict(arrowstyle="->"))

        plt.subplots_adjust(bottom=0.2)
        plt.suptitle(t='Average %d days amount for %s : %s' % (period_days, cat_name, str(avg_weight)[:5]),
                     x=0.65)
        plt.savefig('temp_%s.png' % user_db_id)
        plt.close()
