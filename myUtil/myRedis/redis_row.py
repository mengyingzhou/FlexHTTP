import redis


# Redis Hash
class RedisRow:

    def __init__(self, connection_pool, prime_key):
        self.server = redis.Redis(connection_pool=connection_pool)
        self.prime_key = prime_key

    def add_val(self, row_vals: dict):
        self.server.hmset(self.prime_key, row_vals)

    def update_val(self, updated_vals: dict):
        self.server.hmset(self.prime_key, updated_vals)

    def get_val_of_key(self, key):
        return self.server.hget(self.prime_key, key)

    def get_val_dict(self) -> dict:
        return self.server.hgetall(self.prime_key)
