def nway_implied_probs(odds_list, prnt=False):
    implied_probas = []

    for odds in odds_list:
        if odds < 0:
            implied_proba = (-1. * odds) / (-1 * odds + 100)
        else:
            implied_proba = 100. / (odds + 100)
        implied_probas.append(implied_proba)

    total_implied = sum(implied_probas)
    implied_probas_novig = [ip / total_implied for ip in implied_probas]

    if prnt:
        print("Implied probabilities: %s" % ", ".join(["%.2f%%" % (100 * ip_novig) for ip_novig in implied_probas_novig]))
        print("Vig: %.2f%%" % (100 * (total_implied - 1)))

    return implied_probas_novig, total_implied - 1


def _bet_exp_val(odds, proba):
    if odds < 0:
        mult = 1 + 100 / -odds
    else:
        mult = 1 + odds / 100

    return mult * proba


def bets_exp_val(odds_list, probas):
    return [_bet_exp_val(odds, proba) for odds, proba in zip(odds_list, probas)]


def ml_str(ml_num):
    if ml_num > 100:
        return "+%s" % str(ml_num)
    elif ml_num == 100:
        return "EVEN"
    else:
        return str(ml_num)


def dec_to_amer(dec_odds):
    if dec_odds >= 2.0:
        return 100 * (dec_odds - 1)
    else:
        return -100 / (dec_odds - 1)


def fmt_lines_exp_vals(players, lines, exp_vals, vs_str=' vs. '):
    lines_strs = []
    exp_vals_strs = []
    for plyr, line, exp_val in zip(players, lines, exp_vals):
        line_str = '{0} ({1})'.format(plyr, ml_str(line))
        lines_strs.append(line_str)

        exp_val_str = '{0:0.3f}'.format(exp_val).center(len(line_str))
        exp_vals_strs.append(exp_val_str)

    out_lines_str = vs_str.join(lines_strs)
    out_expvals_str = (len(vs_str) * ' ').join(exp_vals_strs)

    return out_lines_str + '\n' + out_expvals_str
