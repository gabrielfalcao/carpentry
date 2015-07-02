#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os as original_os
from subprocess import CalledProcessError
from datetime import datetime as original_datetime
from mock import Mock, patch, call
from subprocess import STDOUT, PIPE
from carpentry.workers.steps import run_command
from carpentry.workers.steps import stream_output
from carpentry.workers.steps import get_build_from_instructions
from carpentry.workers.steps import set_build_status
from carpentry.workers.steps import PrepareSSHKey
from carpentry.workers.steps import PushKeyToGithub
from carpentry.workers.steps import response_did_succeed


@patch('carpentry.workers.steps.Popen')
def test_run_command(Popen):
    ("run_command() should return a Popen() object")

    # Given that I call run_command
    result = run_command(
        'ls -l',
        '/chdir/sandbox',
        {
            'PATH': '/chdir/sandbox/bin'
        }
    )

    # When it should return a Popen object
    result.should.equal(Popen.return_value)

    # Then it should
    Popen.assert_called_once_with(
        'ls -l',
        shell=True,
        env={
            'PATH': '/chdir/sandbox/bin'
        },
        cwd='/chdir/sandbox',
        stderr=STDOUT,
        stdout=PIPE
    )


@patch('carpentry.workers.steps.logging')
@patch('carpentry.workers.steps.Popen')
def test_run_command_exception(Popen, logging):
    ("run_command() should log an exception when catching one")

    # Given that Popen raises an exception
    Popen.side_effect = ValueError('boom')

    # When I call run_command
    result = run_command(
        'ls -l',
        '/chdir/sandbox',
        {
            'PATH': '/chdir/sandbox/bin'
        }
    )

    # Then it should have returned None
    result.should.be.none

    # And it should have logged the exception
    logging.exception.assert_called_once_with(
        'Failed to run ls -l'
    )


@patch('carpentry.workers.steps.time')
def test_stream_output_stops_on_timeout(time):
    ("stream_output should stop the loop after timing out")

    # Given a timeout of 30 seconds
    timeout = 30
    # And that time.time() returns a timed out value after called for
    # the 4th time
    time.time.side_effect = [
        1000,
        1001,
        1016,
        1050
    ]
    # And that I have a mock of step, build and of process
    step = Mock(name='step')
    build = Mock(name='build')
    build.stdout = ""
    build.stderr = ""
    process = Mock(name='process')

    # And that process.stdout.readline returns a chunk of 512 bytes of
    # string
    process.stdout.readline.side_effect = ['aaaa' * 128, 'bbbb' * 64, 'cccc' * 32, 'dddd' * 32]

    # When I call stream_output
    result = stream_output(
        step,
        process,
        build,
        stdout_chunk_size=512,
        timeout_in_seconds=timeout
    )

    # Then the result should be the string
    result.should.equal(
        (
            ('aaaa' * 128) + ('bbbb' * 64),
            420
        )
    )

    # And the build should have had its stdout updated
    build.stdout.should.equal(('aaaa' * 128) + ('bbbb' * 64) + '\nBuild timed out by 50 seconds')

    # And the stderr should have been updated as well
    build.stderr.should.equal('\nBuild timed out by 50 seconds')

    # And the build should have been saved
    build.save.assert_has_calls([
        call(),
        call(),
    ])

    # And since the build timed out, it terminates the process
    process.terminate.assert_called_once_with()


@patch('carpentry.workers.steps.time')
def test_stream_output_stops_when_no_more_output_is_returned(time):
    ("stream_output should wait for the process and save the "
     "exit code after it stops producing output")

    # Given that time.time() returns a timed out value after called for
    # the 3rd time
    time.time.side_effect = [
        1000,
        1001,
        1016,
        1050
    ]
    # And that I have a mock of step, build and of process
    step = Mock(name='step')
    build = Mock(name='build')
    build.stdout = ""
    build.stderr = ""
    process = Mock(name='process')

    # And that process.wait returns status code 0
    process.wait.return_value = 0

    # And that process.stdout.readline returns an empty string on the 2nd call
    process.stdout.readline.side_effect = [b'the output', b'']

    # When I call stream_output
    result = stream_output(
        step,
        process,
        build,
        timeout_in_seconds=300
    )

    # Then the result should be the string
    result.should.equal(('the output', 0))

    # And the build should have had its stdout updated
    build.stdout.should.equal('the output')

    # And the build should have been saved
    build.save.assert_has_calls([
        call(),
    ])


@patch('carpentry.workers.steps.Build')
def test_get_build_from_instructions(Build):
    ('get_build_from_instructions should return a build '
     'from the id within the payload')

    # Given some fake instructions
    instructions = {'id': 'General-Lee'}

    # When I call get_build_from_instructions
    result = get_build_from_instructions(instructions)

    # Then it should com from Build.objects.get
    result.should.equal(Build.objects.get.return_value)

    # And Build.objects.get was called with the id
    Build.objects.get.assert_called_once_with(
        id='General-Lee')


@patch('carpentry.workers.steps.get_build_from_instructions')
def test_set_build_status(get_build_from_instructions):
    ('set_build_status() should retrieve a build, set its status and save it')

    # Given that get_build_from_instructions is mocked
    build = get_build_from_instructions.return_value

    # And that I have a payload of build instructions
    instructions = {
        'user': {
            'github_access_token': 'github-token'
        }
    }

    # When I call set_build_status
    set_build_status(instructions, 'running', 'geronimooooo')

    # Then it should have called get_build_from_instructions
    get_build_from_instructions.assert_called_once_with(
        instructions
    )

    # And build.set_status should have been called with the
    # github_access_token and the given description
    build.set_status.assert_called_once_with(
        'running',
        'github-token',
        'geronimooooo',
    )


def prepare_step_instance(klass):
    consume_queue = Mock(name='consume_queue')
    produce_queue = Mock(name='produce_queue')
    parent = Mock(name='parent_pipeline')
    step = klass(consume_queue, produce_queue, parent)
    step.produce = Mock(name='{0}.produce()'.format(klass))
    return step


# ----------------------------------------
# PrepareSSHKey Step tests
#

@patch('carpentry.workers.steps.os.chmod')
@patch('carpentry.workers.steps.os.path.exists')
@patch('carpentry.workers.steps.io')
def test_prepare_ssh_key_write_file(io, exists, chmod):
    ('PrepareSSHKey#write_file should write the file and '
     'set its mode')
    fd = io.open.return_value.__enter__.return_value

    # Background: os.path.exists returns True
    exists.return_value = True

    # Given a PrepareSSHKey Step instance
    step = prepare_step_instance(PrepareSSHKey)

    # When I call write_file
    step.write_file(
        '/path/to',
        'file.json',
        '{"foobar": true}',
        0755
    )

    # Then the file is written appropriately
    io.open.assert_called_once_with(
        '/path/to/file.json',
        'wb'
    )

    # And it should have written in the fd
    fd.write.assert_has_calls([
        call('{"foobar": true}'),
        call('\n')
    ])

    # And it should have set the file mode
    chmod.assert_called_once_with(
        '/path/to/file.json',
        0755
    )


@patch('carpentry.workers.steps.os.chmod')
@patch('carpentry.workers.steps.os.makedirs')
@patch('carpentry.workers.steps.os.path.exists')
@patch('carpentry.workers.steps.io')
def test_prepare_ssh_key_write_file_when_dir_does_not_exist(io, exists, makedirs, chmod):
    ('PrepareSSHKey#write_file should create the destination '
     'folder if it does not exist')
    fd = io.open.return_value.__enter__.return_value
    exists.return_value = False

    # Given a PrepareSSHKey Step instance
    step = prepare_step_instance(PrepareSSHKey)

    # When I call write_file
    step.write_file(
        '/path/to',
        'file.json',
        '{"foobar": true}',
        0755
    )

    # Then the file is written appropriately
    io.open.assert_called_once_with(
        '/path/to/file.json',
        'wb'
    )

    # And it should have written in the fd
    fd.write.assert_has_calls([
        call('{"foobar": true}'),
        call('\n')
    ])

    # And it should have set the file mode
    chmod.assert_called_once_with(
        '/path/to/file.json',
        0755
    )

    # And the destination folder should have been created
    makedirs.assert_called_once_with('/path/to')


@patch('carpentry.workers.steps.datetime')
@patch('carpentry.workers.steps.check_output')
@patch('carpentry.workers.steps.set_build_status')
@patch('carpentry.workers.steps.get_build_from_instructions')
def test_prepare_ssh_key_consume(get_build_from_instructions,
                                 set_build_status,
                                 check_output,
                                 datetime):
    ('PrepareSSHKey#write_file should create the destination '
     'folder if it does not exist')
    datetime.utcnow.return_value = original_datetime(2015, 6, 27)

    # Given a PrepareSSHKey Step instance
    step = prepare_step_instance(PrepareSSHKey)

    # And some instructions with ssh info
    instructions = {
        'slug': 'foobar',
        'id_rsa_private': 'the private key',
        'id_rsa_public': 'the public key',
        'id_rsa_private_key_path': 'id_rsa_chucknorris',
        'id_rsa_public_key_path': 'id_rsa_chucknorris.pub',
    }

    # When I call consume with those instructions
    step.consume(instructions)

    # Then get_build_from_instructions should have been called with
    # the instructions
    get_build_from_instructions.assert_called_once_with(
        instructions)

    # And set_build_status sets the build to "running" and provides a
    # description with the start time
    set_build_status.assert_called_once_with(
        instructions,
        'running',
        'carpentry build started at 2015/06/27 00:00:00 UTC',
    )


@patch('carpentry.workers.steps.datetime')
@patch('carpentry.workers.steps.check_output')
@patch('carpentry.workers.steps.set_build_status')
@patch('carpentry.workers.steps.get_build_from_instructions')
def test_prepare_ssh_key_consume_missing_private_key(get_build_from_instructions,
                                                     set_build_status,
                                                     check_output,
                                                     datetime):
    ('PrepareSSHKey#write_file should log to the build output and exit if the private key is missing')
    datetime.utcnow.return_value = original_datetime(2015, 6, 27)

    build = get_build_from_instructions.return_value
    # Given a PrepareSSHKey Step instance
    step = prepare_step_instance(PrepareSSHKey)

    # And some instructions with ssh info
    instructions = {
        'builder_id': 'my-happy-builder',
        'slug': 'foobar',
        'id_rsa_public': 'the public key',
        'id_rsa_private_key_path': 'id_rsa_chucknorris',
        'id_rsa_public_key_path': 'id_rsa_chucknorris.pub',
    }

    # When I call consume with those instructions
    step.consume.when.called_with(instructions).should.have.raised(RuntimeError)

    # Then get_build_from_instructions should have been called with
    # the instructions
    get_build_from_instructions.assert_called_once_with(
        instructions)

    # And set_build_status sets the build to "running" and provides a
    # description with the start time
    set_build_status.assert_called_once_with(
        instructions,
        'running',
        'carpentry build started at 2015/06/27 00:00:00 UTC',
    )

    # And the build output should have gotten date
    build.append_to_stdout.assert_has_calls([
        call(u'preparing ssh key...\n'),
        call(u'the builder my-happy-builder does not have a private_key set')
    ])


@patch('carpentry.workers.steps.datetime')
@patch('carpentry.workers.steps.check_output')
@patch('carpentry.workers.steps.set_build_status')
@patch('carpentry.workers.steps.get_build_from_instructions')
def test_prepare_ssh_key_consume_missing_public_key(get_build_from_instructions,
                                                    set_build_status,
                                                    check_output,
                                                    datetime):
    ('PrepareSSHKey#write_file should log to the build output and exit if the public key is missing')
    datetime.utcnow.return_value = original_datetime(2015, 6, 27)

    build = get_build_from_instructions.return_value
    # Given a PrepareSSHKey Step instance
    step = prepare_step_instance(PrepareSSHKey)

    # And some instructions with ssh info
    instructions = {
        'builder_id': 'my-happy-builder',
        'slug': 'foobar',
        'id_rsa_private': 'the private key',
        'id_rsa_private_key_path': 'id_rsa_chucknorris',
        'id_rsa_public_key_path': 'id_rsa_chucknorris.pub',
    }

    # When I call consume with those instructions
    step.consume.when.called_with(instructions).should.have.raised(RuntimeError)

    # Then get_build_from_instructions should have been called with
    # the instructions
    get_build_from_instructions.assert_called_once_with(
        instructions)

    # And set_build_status sets the build to "running" and provides a
    # description with the start time
    set_build_status.assert_called_once_with(
        instructions,
        'running',
        'carpentry build started at 2015/06/27 00:00:00 UTC',
    )

    # And the build output should have gotten date
    build.append_to_stdout.assert_has_calls([
        call(u'preparing ssh key...\n'),
        call(u'the builder my-happy-builder does not have a public_key set')
    ])


@patch('carpentry.workers.steps.datetime')
@patch('carpentry.workers.steps.check_output')
@patch('carpentry.workers.steps.set_build_status')
@patch('carpentry.workers.steps.get_build_from_instructions')
def test_prepare_ssh_key_consume_ssh_add_failed(
        get_build_from_instructions,
        set_build_status,
        check_output,
        datetime):
    ('PrepareSSHKey#write_file should save the '
     'output of error details when ssh-add failed')
    datetime.utcnow.return_value = original_datetime(2015, 6, 27)

    check_output.side_effect = CalledProcessError(1, 'ssh-add /path/to/key', 'boom')

    # Given a PrepareSSHKey Step instance
    step = prepare_step_instance(PrepareSSHKey)

    # And some instructions with ssh info
    instructions = {
        'slug': 'foobar',
        'id_rsa_private': 'the private key',
        'id_rsa_public': 'the public key',
        'id_rsa_private_key_path': 'id_rsa_chucknorris',
        'id_rsa_public_key_path': 'id_rsa_chucknorris.pub',
    }

    # When I call consume with those instructions
    step.consume(instructions)

    # Then get_build_from_instructions should have been called with
    # the instructions
    get_build_from_instructions.assert_called_once_with(
        instructions)

    # And set_build_status sets the build to "running" and provides a
    # description with the start time
    set_build_status.assert_called_once_with(
        instructions,
        'running',
        'carpentry build started at 2015/06/27 00:00:00 UTC',
    )


def test_response_did_succeed_ok():
    ('response_did_succeed should return True if response is 200-ish')

    class Response:
        def __init__(self, status_code):
            self.status_code = status_code

    response_did_succeed(Response('200')).should.be.true
    response_did_succeed(Response('201')).should.be.true
    response_did_succeed(Response('202')).should.be.true
    response_did_succeed(Response('204')).should.be.true
    response_did_succeed(Response('205')).should.be.true
    response_did_succeed(Response('206')).should.be.true

    response_did_succeed(Response('304')).should.be.false
    response_did_succeed(Response('302')).should.be.false
    response_did_succeed(Response('400')).should.be.false
    response_did_succeed(Response('500')).should.be.false
    response_did_succeed(Response('404')).should.be.false
    response_did_succeed(Response('403')).should.be.false


@patch('carpentry.workers.steps.json')
@patch('carpentry.workers.steps.requests')
def test_push_keys_into_api_and_get_response(requests, json):
    ('PushKeyToGithub#push_keys_into_api_and_get_response()')

    # Given an instance of
    pusher = prepare_step_instance(PushKeyToGithub)

    # When I call push_keys_into_api_and_get_response
    result = pusher.push_keys_into_api_and_get_response(
        'hello github',
        'gabrielfalcao',
        'go-horse',
        'ssh-rsa blablabla',
        'psssstsecret',
    )

    # Then it should return a response from requests
    result.should.equal(requests.post.return_value)

    # And requests.post should have been called appropriately
    requests.post.assert_called_once_with(
        'https://api.github.com/repos/gabrielfalcao/go-horse/keys',
        headers={
            'Authorization': u'token psssstsecret'
        },
        data=json.dumps.return_value
    )


@patch('carpentry.workers.steps.logging')
def test_dump_error_into_build_output(logging):
    ('PushKeyToGithub#dump_error_into_build_output()')

    build = Mock(name='Build(id=42)')
    response = Mock(name='Response')
    response.text = 'the text'
    response.status_code = 400

    # Given an instance of
    pusher = prepare_step_instance(PushKeyToGithub)

    # When I call push_keys_into_api_and_get_response
    pusher.dump_error_into_build_output(
        build,
        response,
    )

    # And it should append a lot of stuff to the stdout
    build.append_to_stdout.assert_has_calls([
        call(u'failed'),
        call(u'\n--------------------\n'),
        call(u'Failed to push deploy key\n'),
        call(u'RESPONSE:\n\n'),
        call(u'the text'),
        call(u'\n--------------------\n'),
    ])

    logging.error.assert_called_once_with(
        '%s: failed to push deploy key %s',
        400,
        'the text'
    )


@patch('carpentry.workers.steps.get_build_from_instructions')
def test_push_key_consume_no_github_info(get_build_from_instructions):
    ('PushKeyToGithub#consume() when github info is missing')
    build = get_build_from_instructions.return_value

    pusher = prepare_step_instance(PushKeyToGithub)

    instructions = {
        'name': 'casablanca',
        'git_uri': 'git@googlecode.seriously.com/foobar',
    }
    pusher.consume(instructions)

    build.append_to_stdout.assert_called_once_with(
        'casablanca declared an invalid github repo: '
        'git@googlecode.seriously.com/foobar, not '
        'pushing ssh keys as deploy keys'
    )


@patch('carpentry.workers.steps.get_build_from_instructions')
@patch('carpentry.workers.steps.PushKeyToGithub.push_keys_into_api_and_get_response')
def test_push_key_consume_ok(
        push_keys_into_api_and_get_response,
        get_build_from_instructions):
    ('PushKeyToGithub#consume() when should push '
     'the keys to github')
    response = push_keys_into_api_and_get_response.return_value
    response.text = '{"yay": "json"}'
    response.status_code = 201

    build = get_build_from_instructions.return_value

    pusher = prepare_step_instance(PushKeyToGithub)

    instructions = {
        'name': 'casablanca',
        'git_uri': 'git@googlecode.seriously.com/foobar',
        'github_repo_info': {
            'owner': 'gabrielfalcao',
            'name': 'HTTPretty',
        },
        'public_key': 'ssh-rsa 1234blablabla',
        'user': {
            'access_token': 'psssstsecret'
        }
    }
    pusher.consume(instructions)

    build.append_to_stdout.assert_has_calls([
        call(u'pushing key to github...\n'),
        call(u'Keys pushed to github successfully!!!!!')
    ])


@patch('carpentry.workers.steps.get_build_from_instructions')
@patch('carpentry.workers.steps.PushKeyToGithub.push_keys_into_api_and_get_response')
@patch('carpentry.workers.steps.PushKeyToGithub.dump_error_into_build_output')
def test_push_key_consume_failed(
        dump_error_into_build_output,
        push_keys_into_api_and_get_response,
        get_build_from_instructions):
    ('PushKeyToGithub#consume() when should push '
     'the keys to github')
    response = push_keys_into_api_and_get_response.return_value
    response.text = '{"oops": "boom"}'
    response.status_code = 400

    build = get_build_from_instructions.return_value

    pusher = prepare_step_instance(PushKeyToGithub)

    instructions = {
        'name': 'casablanca',
        'git_uri': 'git@googlecode.seriously.com/foobar',
        'github_repo_info': {
            'owner': 'gabrielfalcao',
            'name': 'HTTPretty',
        },
        'public_key': 'ssh-rsa 1234blablabla',
        'user': {
            'access_token': 'psssstsecret'
        }
    }
    pusher.consume(instructions)

    dump_error_into_build_output.assert_called_once_with(
        build,
        response
    )
