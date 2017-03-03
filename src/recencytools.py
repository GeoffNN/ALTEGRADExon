from collections import Counter, defaultdict
import operator
import math
import pandas as pd


def add_time_rank_to_dataframe(df):

    # Set mails with absurd dates to date before any real mail
    min_date_string = '1998-12-20 00:00:01'

    correct_prefix = [chars[0:2] == '00' for chars in list(df['date'])]
    df.loc[correct_prefix, 'date'] = min_date_string

    # Convert dates to timestamps
    df['date'] = pd.to_datetime(df['date'], yearfirst=True)

    # Add time rank column and sort dataframe
    df['time_rank'] = df['date'].rank(ascending=False)
    df = df.sort_values('date')
    return df


def get_frequency_address_books(emails_ids_per_sender, email_df):
    """
    Create address book with frequency information for each user
    @return address_books with sender as key and recipients as ranked list
    """
    address_books = {}
    idx_sender = 0

    for sender, ids in emails_ids_per_sender.items():
        recs_temp = []
        for my_id in ids:
            recipients = email_df[email_df['mid'] == int(my_id)][
                'recipients'].tolist()
            recipients = recipients[0].split(' ')
            # keep only legitimate email addresses
            recipients = [rec for rec in recipients if '@' in rec]
            recs_temp.append(recipients)
        # flatten
        recs_temp = [elt for sublist in recs_temp for elt in sublist]
        # compute recipient counts
        rec_occ = dict(Counter(recs_temp))
        # order by frequency
        sorted_rec_occ = sorted(
            rec_occ.items(), key=operator.itemgetter(1), reverse=True)
        # save
        address_books[sender] = sorted_rec_occ

        if idx_sender % 10 == 0:
            print('processed {nb_sender} senders'.format(nb_sender=idx_sender))
        idx_sender += 1
    return address_books


def get_recency_address_books(emails_ids_per_sender, email_df, beta):
    """
    Create address book with recency information for each user
    @return address_books with sender as key and recipients as ranked list
    """
    address_books = {}
    idx_sender = 0
    email_ranks_dic = get_email_ranks(email_df)
    for sender, ids in emails_ids_per_sender.items():
        recipients_scores = defaultdict(lambda: 0)
        for my_id in ids:
            my_id = int(my_id)
            recency_score = get_email_recency_score(
                email_ranks_dic, my_id, beta)
            recipients = email_df[email_df['mid'] == int(my_id)][
                'recipients'].tolist()
            recipients = recipients[0].split(' ')
            # keep only legitimate email addresses
            recipients = [rec for rec in recipients if '@' in rec]
            for recipient in recipients:
                recipients_scores[recipient] += recency_score
        # flatten
        rec_occ = dict(Counter(recipients_scores))
        # order by frequency
        sorted_rec_occ = sorted(
            rec_occ.items(), key=operator.itemgetter(1), reverse=True)
        # save
        address_books[sender] = sorted_rec_occ

        if idx_sender % 10 == 0:
            print('processed {nb_sender} senders'.format(nb_sender=idx_sender))
        idx_sender += 1
    return address_books


def get_email_ranks(email_df):
    """
    Creates dictionnary that links mid to time rank
    (1 for most recent mail)
    """
    return dict(zip(email_df['mid'], email_df['time_rank']))


def get_email_rank(mid_rank_dic, mid):
    """
    Retrieve email rank for given mid
    """
    return mid_rank_dic[mid]


def get_email_recency_score(mid_rank_dic, mid, beta):
    """
    Compute the recency score for a given mid
    """
    mid_rank = get_email_rank(mid_rank_dic, mid)
    recency_score = math.exp(- mid_rank / beta)
    return recency_score