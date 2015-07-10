angular.module('CarpentryApp.NewBuilder', ['CarpentryApp.Common']).controller('NewBuilderController', function ($rootScope, $scope, $state, $http, $cookies, hotkeys, notify) {
    // 'name': 'Device Management [unit tests]',
    // 'git_uri': 'git@github.com:gabrielfalcao/lettuce.git',
    // 'build_instructions': 'make test',
    $rootScope.resetPollers();
    $scope.saveInProcess = false;
    var DEFAULT_LANGUAGE = "python";
    $scope.builderType = 'native';
    $scope.SHELL_SCRIPT_EXAMPLES = {
        "timeout test": [
            "#!/bin/bash",
            '',
            "for x in `seq 100`; do",
            "    date;",
            "    sleep 0.1;",
            "done"
        ].join('\n'),
        "python": [
            '#!/bin/bash',
            'set -e',
            '',
            'pip install virtualenv',
            'virtualenv .venv',
            'source .venv/bin/activate',
            'pip install -r requirements.txt || echo "skipped development.txt"',
            'pip install -r development.txt || echo "skipped development.txt"',
            'make'
        ].join("\n"),
        "ruby": [
            '#!/bin/bash',
            'set -e',
            '',
            'bundler install',
            'gem install',
            'rake'
        ].join("\n"),
        "nodejs": [
            '#!/bin/bash',
            'set -e',
            '',
            'npm install',
            'npm test',
        ].join("\n"),
        "java": [
            '#!/bin/bash',
            'set -e',
            '',
            'maven install',
        ].join("\n")
    };

    $scope.builder = {
        'generate_ssh_keys': true,
        'loadFromYAML': true,
        'name': '',
        'git_uri': 'git@github.com:',
        'shell_script': $scope.SHELL_SCRIPT_EXAMPLES[DEFAULT_LANGUAGE]
    };

    $scope.doShellScriptExample = function(language){
        $scope.builder.shell_script = $scope.SHELL_SCRIPT_EXAMPLES[language] || "boo hoo :P";
    };
    $scope.createBuilder = function(builder) {
        $scope.saveInProcess = true;

        $http.post('/api/builder', builder).
            success(function(data, status, headers, config) {
                $scope.saveInProcess = false;

                console.log("/api/builder OK");
                $rootScope.go('/');
            }).error(function(data, status){
                $scope.saveInProcess = false;
                if (status !== 502) {
                    notify('Failed to create builder');
                }
                console.log('Failed to create builder', status, data);
            });
    };

    $("#builder_name").typeahead({ source:jQuery.map($rootScope.githubRepositories, function(val){
        return val.name;
    })});
    $("#git_uri").typeahead({ source:jQuery.map($rootScope.githubRepositories, function(val){
        console.log(val.owner.login, val.name, val.ssh_url);
        return val.ssh_url;
    })});
});
