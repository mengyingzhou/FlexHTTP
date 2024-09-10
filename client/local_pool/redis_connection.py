import redis
redis_pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)

table_incr_training = "table_incr_training"
table_request_logs = "table_request_logs"
table_incr_training_with_labels = "table_incr_training_with_labels"
