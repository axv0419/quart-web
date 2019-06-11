import datetime
import time
import sys
import yaml
import json
import collections

from confluent_kafka import Producer,Consumer,KafkaError,TopicPartition

from collections import defaultdict
import argparse
import traceback
import logging
from datetime import datetime, timedelta

from cachetools import cached, LRUCache, TTLCache


LOGGER = logging.getLogger(__file__)

class KafkaConsumer:
    def __init__(self,conf,group_id='kafka-rest-service'):
        conf = dict(conf)
        conf['group.id'] = group_id
        self.consumer = Consumer(conf)
    @cached(cache=TTLCache(maxsize=1024, ttl=60))
    def get_topic_partition_count(self,topic_name):
        cmd = self.consumer.list_topics(topic_name)
        tmd = cmd.topics.get(topic_name,None)
        pcount = 0
        if tmd:
            pcount = len(tmd.partitions)
        return pcount
    # @cached(cache=TTLCache(maxsize=1024, ttl=60))
    def get_topic_offsets(self,topic_name):
        pcount = self.get_topic_partition_count(topic_name)
        if pcount == 0:
            return dict(
                error=f"Requested topic {topic_name} not found", 
                status="ERROR",
                report=None)

        part_status_map = {}
        for p in range(pcount):
            l,h = self.consumer.get_watermark_offsets(TopicPartition(topic_name,p))
            part_status_map[p]=[h,'1 month']

        def get_minute_report(minute,time_text):
            timestamp = (datetime.now() - timedelta(minutes=minute)).timestamp()
            timestamp = int(timestamp)*1000
            partitions = [ TopicPartition(topic_name,p,timestamp) for p in range(pcount)]
            partitions = self.consumer.offsets_for_times(partitions)
            for par in partitions:
                if par.offset > -1 : 
                    part_status_map[par.partition][-1] = time_text

        get_minute_report(60*24*7,'1 week')
        get_minute_report(60*24,'1 day')
        get_minute_report(60, '1 hour')
        get_minute_report(10, '10 minutes')
        get_minute_report(1 ,'1 minute')
                
        part_status_map = {k:list(v) for k,v in part_status_map.items()}
        return dict(
            error=None, 
            status="SUCCESS",
            topic=topic_name,
            offsets=part_status_map)

class KafkaProducer:
    def __init__(self,conf):
        self.producer = Producer(conf)

    @cached(cache=TTLCache(maxsize=1024, ttl=60))
    def get_topic_partition_count(self,topic_name):
        cmd = self.producer.list_topics(topic_name)
        tmd = cmd.topics.get(topic_name,None)
        pcount = 0
        if tmd:
            pcount = len(tmd.partitions)
        return pcount

    def send_records(self,topic,records,headers):
        responses = []
        def delivery_report(err, msg):
            """ Called once for each message produced to indicate delivery result.
                Triggered by poll() or flush(). """
            if err is not None:
                LOGGER.info('Message delivery failed: {}'.format(err))
            else:
                LOGGER.info('Message delivered {} {} {} [{}] {}'.format( msg.timestamp(),msg.offset(), msg.topic(), msg.partition(), msg.key()))

            keystr = None if err or not msg.key() else msg.key().decode('UTF-8') 
            if not err:
                report=dict(timestamp=msg.timestamp()[1],partition=msg.partition(),\
                    offset=msg.offset(),key=keystr)
            else:
                report=dict(error = f"{err}",status="PRODUCER_ERROR")
            responses.append(report)

        partition_count = self.get_topic_partition_count(topic)
        if not partition_count:
            LOGGER.warn(f"Requested topic {topic} does not exist")
            return "TOPIC_NOT_FOUND",dict(reason=f"Topic {topic} not found or not accessible to current user")

        LOGGER.info(f"sending records - {records}")

        for record in records:
            data = json.dumps(record["value"])
            key = record.get('key')
            partition = record.get('partition',None)
            if partition:
                try:
                    partition = int(partition)
                except:
                    partition = 0
            if partition:
                record_partition =  partition % partition_count
                self.producer.produce(topic,value=data,partition=record_partition, key=key, callback=delivery_report,headers=headers)
            else:
                self.producer.produce(topic, data, key=key, callback=delivery_report,headers=headers)
            self.producer.poll(.01)
        self.producer.flush()
        LOGGER.info(f"Responses - {responses}")
        retval = {"key_schema_id": None,"value_schema_id": None,"offsets": responses}

        return None, responses

if __name__ == '__main__':
    _KP = KafkaProducer({'bootstrap.servers':'libra:9092'})

