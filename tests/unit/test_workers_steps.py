#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
from mock import Mock, patch, call
from subprocess import STDOUT, PIPE
from carpentry.workers.steps import run_command
from carpentry.workers.steps import stream_output
from carpentry.workers.steps import get_build_from_instructions
from carpentry.workers.steps import set_build_status
from carpentry.workers.steps import PrepareSSHKey


@patch('carpentry.workers.steps.Popen')
def test_run_command(Popen):
    ("run_command should return a Popen() object")

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
    ("run_command should log an exception when catching one")

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

@patch('carpentry.workers.steps.os')
@patch('carpentry.workers.steps.io')
def test_prepare_ssh_key_write_file(io, os):
    ('PrepareSSHKey#write_file should write the file and '
     'set its mode')
    fd = io.open.return_value.__enter__.return_value

    # Background: os.path.exists returns True
    os.path.join = lambda *args: "/".join(map(lambda x: x.strip('/'), args))

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
        'path/to/file.json',
        'wb'
    )

    # And it should have written in the fd
    fd.write.assert_has_calls([
        call('{"foobar": true}'),
        call('\n')
    ])
