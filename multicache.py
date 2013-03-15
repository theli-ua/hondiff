"""
    Appswell Multicache Lib

    A memcache wrapper for caching larger sequences. Currently only supports
    these methods:
        - set
        - get

    Eventually, it should map all the memcache client functions at:
    http://code.google.com/appengine/docs/python/memcache/clientclass.html

    USAGE
    from lib import multicache
    multicache.set(cache_key, cache_data, cache_len)
"""
#
# Imports
#
# Python Standard
import logging
import pickle
from math import (ceil)

# Google App Engine
from google.appengine.api import (memcache)


#
# Storage Methods (set)
#
def set(key, value, duration=3600*24):
    if not is_too_large(value):
        memcache.set(key, value, duration)
    else:
        set_as_shards(key, value, duration)

def is_too_large(cache_value):
    cache_size = len(serialize_object(cache_value))
    too_large = cache_size > (memcache.MAX_VALUE_SIZE / 1.5)
    logging.info('cache value size [%s] too large: %s' % (cache_size, too_large))
    return too_large

def set_as_shards(key, value, duration):
    """Note: keys must be zero-filled so index can be reordered"""
    if type(value) != str:
        value = serialize_object(value)

    # split into shards
    num_shards = estimate_num_shards(value)
    shard_list = split_string_into_parts(value, num_shards)
    logging.info('splitting multicache value into %s shards' % (num_shards))

    # index shards
    cache_dict = {}
    i = 0
    for shard in shard_list:
        shard_key = '%s__%06d' % (key, i)
        cache_dict[shard_key] = shard
        i += 1

    # save shard index
    shard_index = {
        '__is_multicache__' : True,
        '__key_list__' : cache_dict.keys(),
    }
    memcache_return = memcache.set(key, shard_index, duration)

    # save shards
    for shard_key in cache_dict:
        logging.info([shard_key, len(cache_dict[shard_key])])
        memcache.set(shard_key, cache_dict[shard_key], duration)

    return memcache_return

def serialize_object(o):
    return pickle.dumps(o)

def estimate_num_shards(value):
    """calculates limit then halves it just to be safe"""
    obj_size = len(str(value))
    num_shards = ceil((obj_size * 2.0) / memcache.MAX_VALUE_SIZE)
    return int(num_shards)

def split_string_into_parts(s, num_parts):
    return split_list_into_num_lists(s, num_parts)

def split_list_into_num_lists(list_, num):
    """ Yield num successive chunks from list_.
    ref: http://stackoverflow.com/questions/2130016/ """
    newn = int(1.0 * len(list_) / num + 0.5)
    for i in xrange(0, num-1):
        yield list_[i*newn:i*newn+newn]
    yield list_[num*newn-newn:]

#
# Retrieval Methods (get)
#
def get(key, default=None):
    value = memcache.get(key)

    if not value:
        return None
    elif is_multicache_value(value):
        key_list = value.get('__key_list__')
        logging.info(key_list)
        try:
            return get_as_shards(key_list)
        except LostShard, e:
            logging.error(e)
            return None
    else:
        return value

def is_multicache_value(value):
    return type(value) == dict and value.get('__is_multicache__')

def get_as_shards(key_list):
    shard_list = []

    # must resort key list to get serial in right order
    key_list.sort()

    for key in key_list:
        shard_serial_str = memcache.get(key)
        if not shard_serial_str:
            raise LostShard('no shard for key: %s' % (key))
        shard_list.append(shard_serial_str)

    # return reintegrated value
    serialized_object = ''.join(shard_list)
    return pickle.loads(serialized_object)
