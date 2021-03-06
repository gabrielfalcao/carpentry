angular.module('CarpentryApp', [
    'ngCookies',
    'ui.router',
    'ui.bootstrap.progressbar',
    'cfp.hotkeys',
    'cgNotify',
    /* 'btford.socket-io', */
    'angular-loading-bar',
    'luegg.directives',
    'CarpentryApp.Common',
    'CarpentryApp.Index',
    'CarpentryApp.NewBuilder',
    'CarpentryApp.EditBuilder',
    'CarpentryApp.Build',
    'CarpentryApp.Preferences',
    'CarpentryApp.Fullscreen',
    'CarpentryApp.ShowBuilder',
    'CarpentryApp.UserProfile',
    'CarpentryApp.Docker',
    'CarpentryApp.Splash'
]).filter('truncate', function (){
    return function (input, chars, breakOnWord) {
        if (isNaN(chars)) return input;
        if (chars <= 0) return '';
        if (input && input.length > chars) {
            input = input.substring(0, chars);

            if (!breakOnWord) {
                var lastspace = input.lastIndexOf(' ');
                //get last space
                if (lastspace !== -1) {
                    input = input.substr(0, lastspace);
                }
            } else {
                while(input.charAt(input.length-1) === ' '){
                    input = input.substr(0, input.length -1);
                }
            }
            return input;
        }
        return input;
    };
}).config(function ($stateProvider, $urlRouterProvider, cfpLoadingBarProvider) {
    cfpLoadingBarProvider.includeBar = false;
    cfpLoadingBarProvider.includeSpinner = false;
    cfpLoadingBarProvider.latencyThreshold = 10;

    $stateProvider.state('index', {
        url: '/',
        templateUrl: '/assets/js/templates/index.html',
        controller: 'IndexController'
    }).state('new-builder', {
        url: '/new-builder',
        templateUrl: '/assets/js/templates/new-builder.html',
        controller: 'NewBuilderController'
    }).state('edit-builder', {
        url: '/builder/:builder_id/edit',
        templateUrl: '/assets/js/templates/edit-builder.html',
        controller: 'EditBuilderController'
    }).state('build-detail', {
        url: '/builder/:builder_id/build/:build_id',
        templateUrl: '/assets/js/templates/build-detail.html',
        controller: 'BuildController'
    }).state('builder-detail', {
        url: '/builder/:builder_id',
        templateUrl: '/assets/js/templates/show-builder.html',
        controller: 'ShowBuilderController'
    }).state('preferences', {
        url: '/preferences',
        templateUrl: '/assets/js/templates/preferences.html',
        controller: 'PreferencesController'
    }).state('fullscreen', {
        url: '/fullscreen',
        templateUrl: '/assets/js/templates/fullscreen.html',
        controller: 'FullscreenController'
    }).state('splash', {
        url: '/splash',
        templateUrl: '/assets/js/templates/splash.html',
        controller: 'SplashController'
    }).state('docker', {
        url: '/docker',
        templateUrl: '/assets/js/templates/docker.html',
        controller: 'DockerController'
    }).state('user-profile', {
        url: '/profile',
        templateUrl: '/assets/js/templates/profile.html',
        controller: 'UserProfileController'
    }).state('not-found', {
        url: '/not-found',
        templateUrl: '/assets/js/templates/404.html'
    });
    $urlRouterProvider.otherwise('/splash');
}).run(function ($rootScope, $state, $templateCache, $http, notify, $location, hotkeys) {
    var appLocation = /[#](.*)/.exec(location.href);
    if (appLocation) {
        $rootScope.originalUrl = appLocation[1];
    } else {
        $rootScope.originalUrl = "/";
    }
    $rootScope.githubRepositories = [];

    $rootScope.resetPollers = function(){
        clearInterval($rootScope.indexPoller);
        clearInterval($rootScope.builderPoller);
        clearInterval($rootScope.buildPoller);
        clearInterval($rootScope.refreshDockerImagesPoller);
        clearInterval($rootScope.refreshDockerContainersPoller);

        $rootScope.indexPoller = 0;
        $rootScope.builderPoller = 0;
        $rootScope.buildPoller = 0;
        $rootScope.refreshDockerImagesPoller = 0;
        $rootScope.refreshDockerContainersPoller = 0;
    };
    $rootScope.go = function (path) {
        $location.path(path);
    };
    $rootScope.$on('$routeChangeStart', function(event, next, current) {
        if (typeof(current) !== 'undefined'){
            $templateCache.remove(current.templateUrl);
        }
    });
    $rootScope.$on('$viewContentLoaded', function() {
        $templateCache.removeAll();
    });

    $http.defaults.headers.common.Authorization = 'Bearer: ' + window.CARPENTRY_TOKEN;
    $rootScope.hasToken = ((window.CARPENTRY_TOKEN + "").length > 0);
    $rootScope.isAuthenticated = $rootScope.hasToken;
    notify.config({
        "templateUrl": "/assets/vendor/angular-notify/angular-notify.html"
    });

    /* // github-based authentication confirmation by retrieving user data
       $rootScope.isAuthenticated = false;
    */
    if ($rootScope.hasToken) {
        $http.get("/api/user").success(function(data, status){
            $rootScope.user = data;
            $rootScope.isAuthenticated = true;
            // console.log("GitHub Metadata", data);
            $rootScope.go($rootScope.originalUrl);
        }).error(function(data, status){
            location.href = "/logout";
        });
    }
    $rootScope.getDockerImages = function(){
        $http
            .get('/api/docker/images')
            .success(function(data, status, headers, config) {
                $rootScope.dockerImages = data;
                // console.log(data);
            })

            .error(function(data, status, headers, config) {
                // console.log('failed to list docker images ');
                notify('failed to list docker images');
            });
    };
    $rootScope.getDockerContainers = function(){
        $http
            .get('/api/docker/containers')
            .success(function(data, status, headers, config) {
                $rootScope.dockerContainers = data;
                // console.log(data);
            })

            .error(function(data, status, headers, config) {
                // console.log('failed to list docker containers ');
                notify('failed to list docker containers');
            });
    };
    $rootScope.getRepositories = function(){
        $http
            .get('/api/github/repos')
            .success(function(data, status, headers, config) {
                console.log(data);
                $rootScope.githubRepositories = data;
            })
            .error(function(data, status, headers, config) {
                // console.log('failed to list docker images ');
                if (status >= 500) {
                    notify('failed to list github repositories');
                }
            });
    };

    $rootScope.defaultErrorHandler = function(data, status, headers, config) {
        if (status === 401) {
            go("/splash");
        } else {
            if (data.error) {
                notify("ERROR: " + data.error);
            } else {
                // console.log("ERROR", data, status);
            }
        }
    };

    $rootScope.getRepositories();
}).directive('showtab', function () {
    return {
        link: function (scope, element, attrs) {
            element.click(function(e) {
                e.preventDefault();
                jQuery(element).tab('show');
            });
        }
    }
}).directive('navbar', function ($rootScope, $state, $location) {
    return {
        restrict: 'E',
        templateUrl: '/assets/js/templates/navbar.html',
        link: function (scope, element, attrs) {
        }
    }
}).controller('CarpentryMainCtrl', function ($scope, $http, $location, $rootScope, hotkeys, $state, $templateCache) {
    $rootScope.buildCache = {};

    $rootScope.triggerBuild = function(builder, stay){
        // console.log( "triggerBuild");
        $http
            .post('/api/builder/' + builder.id + '/build')

            .success(function(data, status, headers, config) {
                if (stay !== true) {
                    $rootScope.go('/builder/' + builder.id + '/build/' + data.id);
                }
            })

            .error(function(data, status, headers, config) {
                for (var x in data) {
                    var build = data[x];
                    $rootScope.buildCache[builderId][build.id] = build;
                }
            });

    };

    $rootScope.logout = function(){
        function do_logout() {
            location.href='/logout';
        }
        $http.get("/logout").success(do_logout).error(do_logout);
        do_logout();
    }

    $rootScope.mainPage = function(){
        location.href='/';
    }

    $rootScope.refresh = function(ok){
        $http.get("/api/builders").
            success(function(data, status, headers, config) {
                $rootScope.builders = Builder.fromList(data);
                ok(data, status, headers, config);
            }).error($rootScope.defaultErrorHandler);
    };

    $rootScope.refresh();
    hotkeys.add({
        combo: 'n',
        description: 'create a new builder',
        callback: function () {
            $rootScope.go('/new-builder');
        }
    });
    hotkeys.add({
        combo: 'f',
        description: 'fullscreen',
        callback: function () {
            $rootScope.go('/fullscreen');
        }
    });
    hotkeys.add({
        combo: 'D',
        description: 'docker management',
        callback: function () {
            $rootScope.go('/docker');
        }
    });
    hotkeys.add({
        combo: 'p',
        description: 'preferences',
        callback: function () {
            $rootScope.go('/preferences');
        }
    });
    hotkeys.add({
        combo: 'd',
        description: 'dashboard',
        callback: function () {
            $rootScope.go('/');
        }
    });
    hotkeys.add({
        combo: 'r',
        description: 'stop http requests',
        callback: function () {
            $rootScope.resetPollers();
        }
    });
    hotkeys.add({
        combo: 'R',
        description: 'refresh browser',
        callback: function () {
            location.href = "/?refresh=" + (new Date()).getTime();
        }
    });
    hotkeys.add({
        combo: 'esc',
        description: 'previous screen',
        callback: function () {
            if ($rootScope.stateStack.length > 0) {
                var name = $rootScope.stateStack.pop();
                $rootScope.go(name);
                $rootScope.stateStack.pop();
            } else {
                $rootScope.go('/');
            }
            // console.log('state stack', $rootScope.stateStack);
        }
    });
    $rootScope.previousState;
    $rootScope.currentState;
    $rootScope.stateStack = [];
    $rootScope.$on('$stateChangeSuccess', function (ev, to, toParams, from, fromParams) {
        if ($rootScope.previousState !== from.name) {
            $rootScope.previousState = from.name || '/';
            $rootScope.currentState = to.name || '/';
        }
        $rootScope.stateStack.push($rootScope.currentState);
    });
    $rootScope.$state = $state;
    $rootScope.$on('$viewContentLoaded', function () {
        $templateCache.removeAll();
    });
});
