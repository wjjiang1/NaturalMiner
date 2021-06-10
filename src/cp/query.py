'''
Created on Jun 5, 2021

@author: immanueltrummer
'''
class QueryEngine():
    """ Processes queries distinguishing entities from others. """
    
    def __init__(self, connection, table, cmp_pred):
        """ Initialize query engine for specific connection.
        
        Args:
            connection: connection to database
            table: queries refer to this table
            cmp_pred: use for comparisons
        """
        self.connection = connection
        self.table = table
        self.cmp_pred = cmp_pred
    
    def rel_avg(self, eq_preds, agg_col):
        """ Relative average of focus entity in given data scope. 
        
        Args:
            eq_preds: equality predicates definint scope
            agg_col: consider averages in this column
            
        Returns:
            Ratio of entity to general average
        """
        entity_avg = self.avg(eq_preds, self.cmp_pred, agg_col)
        general_avg = self.avg(eq_preds, 'true', agg_col)
        
        f_gen_avg = max(0.0001, float(general_avg))
        return float(entity_avg) / f_gen_avg
    
    def avg(self, eq_preds, pred, agg_col):
        """ Calculate average over aggregation column in scope. 
        
        Args:
            eq_preds: equality predicates as column-value pairs
            pred: SQL string representing predicate
            agg_col: calculate average for this column
            
        Returns:
            Average over aggregation column for satisfying rows
        """
        q_parts = [f'select avg({agg_col}) from {self.table} where TRUE'] 
        q_parts += [f"{c}='{v}'" for c, v in eq_preds]
        q_parts += [pred]
        query = ' AND '.join(q_parts)
        
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            avg = cursor.fetchone()[0]
            
        return avg