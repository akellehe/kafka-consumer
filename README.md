# Kafka Consumers in Python3.7

A simple way to get up and running is with `docker-compose`. There are a lot of great container images for python. The one I'm using is `python:3.7-slim`. It's much lighter weight than `python:3.7`. 

This project is just to illustrate some good design principles when you're writing consumers for Kafka.

## Getting Started

Just clone the repo and then say `docker-compose up`. I keep having to run that twice for whatever reason for things to work properly.

I've actually had more luck by running `docker-compose run consumer`. 

Anyway, this obviously requires `docker` and `docker-compose`. 

## A Simple HTTP Service

A common use case is to call an API over HTTP. You can write this in just a few lines if you don't care about robustness. To make it more reliable, though, it takes some handling. For even such a simple service this can be a little complicated.

If you would like to follow along; you can check out `consumer/main.py`

### Poll vs Push

Kafka's model for consuming messages is poll based. The rationale is that you grab messages when you're ready to do more work. That might seem like it would defeat the purpose of using coroutines, but there is still a lot you can do asynchronously.

### Connecting and Reconnecting

There's no guarantee that the Kafka service will be available at the time your process starts up. There's also no guarantee it will _stay_ up while your process is running.

In order to connect to initialize you can retry until you succeed. See the `get_consumer` method 

If there is a connection error while you're processing you can use the `.error()` method on the consumer to find it and simply continue what you were doing. It's polite to back off with a `time.sleep()` or, even better, `asyncio.sleep()`. 

### Cleanup

The Kafka consumer maintains some state as it's running. In order to clean it up you have to call `.close()` when your program exits. The `IOLoop` also maintains access to resources. Of primary concern are file descriptors used for event handling at the operating system level. 

Killing your process with `kill -9` will cause those file descriptors to be left laying around, or even corrupted. That can cause churning when you attempt to restart, and a host of other problems. Stopping the `IOLoop` gracefully is a simple solution.

You can find the code to do that in `handle_disconnect()` and that's installed at the time `SIGTERM` is thrown. That's a common one for process managers like `supervisor` to use to tell your process it's time to stop doing what it's doing.

### Asynchronous Message Handling

You don't really need to worry about pulling a bunch of messages from Kafka quickly. Confluent's client pre-fetches messages in another thread to make them available to you when you call `.poll()`. Unlike many clients, you also don't need to worry about missing heartbeats unless your task is particularly CPU intense. That's because when that other thread fetches messages it also signals the process is still alive.

Python3 coroutines use the `async/await` syntax to switch between frames. Unlike some other implementations (like tornado) if you want to get _real_ concurrency you have to invoke many coroutines at once and _then_ call `run_forever`. 

One alternative to this is collecting batches of `asyncio.Task` objects by calling `asyncio.create_task(coro)` and then calling `asyncio.gather(aws)` or `asyncio.wait(...)` to run them at once. This lets you batch stuff, but you won't be able to continuously reach your host's full resource utilization for the python process (which is still subject to the GIL no matter how many threads you run) that way.


