import redis
redis_pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)

table_global_trace = "table_global_trace"
table_global_trace_with_labels = "table_global_trace_with_labels"

