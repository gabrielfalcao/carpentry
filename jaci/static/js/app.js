angular.module("JaciApp", [
    "ngCookies",
    "ui.router",
    "cfp.hotkeys",
    "cgNotify",
    'luegg.directives',
    "JaciApp.Common",
    "JaciApp.Index",
    "JaciApp.NewBuilder",
    "JaciApp.Build",
    "JaciApp.Preferences",
    "JaciApp.Fullscreen",
    "JaciApp.Splash"
]).config(function($stateProvider, $urlRouterProvider) {
    $stateProvider
        .state("index", {
            url: "/",
            templateUrl: "/assets/js/templates/index.html",
            controller: "IndexController"
        })
        .state("new-builder", {
            url: "/new-builder",
            templateUrl: "/assets/js/templates/new-builder.html",
            controller: "NewBuilderController"
        })
        .state("build-detail", {
            url: "/build/:owner/:project/:buildid",
            templateUrl: "/assets/js/templates/build-detail.html",
            controller: "BuildController"
        })
        .state("preferences", {
            url: "/preferences",
            templateUrl: "/assets/js/templates/preferences.html",
            controller: "PreferencesController"
        })
        .state("fullscreen", {
            url: "/fullscreen",
            templateUrl: "/assets/js/templates/fullscreen.html",
            controller: "FullscreenController"
        })
        .state("splash", {
            url: "/splash",
            templateUrl: "/assets/js/templates/splash.html",
            controller: "SplashController"
        })
        .state("not-found", {
            url: "/not-found",
            templateUrl: "/assets/js/templates/404.html"
        });
    $urlRouterProvider.otherwise("/");

}).run(function($rootScope, $state, $templateCache, $http, notify, hotkeys){
})
    .directive('navbar', function($rootScope, $state, $location) {
        return {
            restrict: 'E',
            templateUrl: "/assets/js/templates/navbar.html",
            link: function (scope, element, attrs) {
            }
        }
    })
    .controller("JaciMainCtrl", function($scope, $http, $location, $rootScope, hotkeys, $state, $templateCache){
        $rootScope.go = function ( path ) {
            $location.path( path );
        };

        hotkeys.add({
            combo: 'n',
            description: 'create a new builder',
            callback: function(){
                $rootScope.go("/new-builder");
            }
        });
        hotkeys.add({
            combo: 'f',
            description: 'fullscreen',
            callback: function(){
                $rootScope.go("/fullscreen");
            }
        });
        hotkeys.add({
            combo: 'p',
            description: 'preferences',
            callback: function(){
                $rootScope.go("/preferences");
            }
        });
        hotkeys.add({
            combo: 'f',
            description: 'dashboard',
            callback: function(){
                $rootScope.go("/");
            }
        });

        hotkeys.add({
            combo: 'esc',
            description: 'previous screen',
            callback: function(){
                if ($rootScope.stateStack.length > 0) {
                    var name = $rootScope.stateStack.pop();
                    $rootScope.go(name);
                    $rootScope.stateStack.pop();

                } else {
                    $rootScope.go("index");
                }
                console.log("state stack", $rootScope.stateStack);
            }
        });
        $rootScope.previousState;
        $rootScope.currentState;
        $rootScope.stateStack = [];
        $rootScope.$on('$stateChangeSuccess', function(ev, to, toParams, from, fromParams) {
            if ($rootScope.previousState !== from.name) {
                $rootScope.previousState = from.name || "/";
                $rootScope.currentState = to.name || "/";
            }
            $rootScope.stateStack.push($rootScope.currentState);
            console.log("state stack", $rootScope.stateStack);
        });
        $rootScope.$state = $state;
        $rootScope.$on("$viewContentLoaded", function() {
            $templateCache.removeAll();
        });
        $('pre code').each(function(i, block) {
            hljs.highlightBlock(block);
        });


    });
