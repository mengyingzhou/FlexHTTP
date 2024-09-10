import redis


# Redis Set
class RedisTable:

    def __init__(self, connection_pool, name):
        self.server = redis.Redis(connection_pool=connection_pool)
        self.name = name

    def add_row(self, row_prime_key):
        self.server.sadd(self.name, row_prime_key)

    def update_row(self, updated_row_prime_key):
        self.server.sadd(self.name, updated_row_prime_key)

    def search_row(self, row_prime_key):
        return self.server.sismember(self.name, row_prime_key)

    def get_all_rows(self):
        return self.server.smembers(self.name)

    def delete_row(self, deleted_prime_key):
        self.server.srem(self.name, deleted_prime_key)
