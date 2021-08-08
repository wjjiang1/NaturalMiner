'''
Created on Jul 31, 2021

@author: immanueltrummer
'''
from cp.cache.common import AggCache
from cp.sql.query import AggQuery, GroupQuery
import logging
import time

class DynamicCache(AggCache):
    """ Cache whose content is updated dynamically. """
    
    def __init__(self, connection, table, cmp_pred):
        """ Initializes proactive cache.
        
        Args:
            connection: connection to database
            table: name of source table
            cmp_pred: predicate used for comparisons
        """
        self.connection = connection
        self.table = table
        self.cmp_pred = cmp_pred
        self.q_to_r = {}

    def cache(self, aggs, preds):
        """ Cache results for given aggregates and predicates. 
        
        Args:
            aggs: aggregates to cache
            preds: predicates to cache
        """
        if preds:
            dims = {p[0] for p in next(iter(preds))}
        else:
            dims = {}

        g_query = GroupQuery(self.table, dims, self.cmp_pred)
        sql = g_query.sql()
        logging.debug(f'About to fill cache with SQL "{sql}"')
        
        with self.connection.cursor() as cursor:
            start_s = time.time()
            cursor.execute(sql)
            total_s = time.time() - start_s
            logging.debug(f'Time: {total_s} s for query {sql}')
            rows = cursor.fetchall()
            self._extract_results(aggs, preds, rows)

    def can_answer(self, query):
        """ Check if query result is cached.
        
        Args:
            query: look for this query's result
        
        Returns:
            true iff query result is cached
        """
        return query in self.q_to_r
        
    def get_result(self, query):
        """ Get cached result for given query.
        
        Args:
            query: aggregation query for lookup
        
        Returns:
            result for given aggregation query
        """
        return self.q_to_r[query]

    def _extract_results(self, aggs, preds, rows):
        """ Extracts new cache entries from query result.
        
        Args:
            aggs: aggregation columns
            preds: predicate groups used for query
            rows: result rows of caching query
        """
        if preds:
            dims = {p[0] for p in next(iter(preds))}
        else:
            dims = {}

        for r in rows:
            cmp_c = r['cmp_c']
            if cmp_c > 0:
                c = r['c']
                for agg in aggs:
                    s = r[f's_{agg}']
                    if s is not None and s > 0:
                        cmp_s = r[f'cmp_s_{agg}']
                        eq_preds = [(d, r[d]) for d in dims]
                        q = AggQuery(self.table, frozenset(eq_preds), 
                                     self.cmp_pred, agg)
                        rel_avg = (cmp_s/cmp_c)/(s/c)
                        self.q_to_r[q] = rel_avg
                        
        for agg in aggs:
            for p_group in preds:
                q = AggQuery(self.table, frozenset(p_group), self.cmp_pred, agg)
                if not self.can_answer(q):
                    self.q_to_r[q] = None