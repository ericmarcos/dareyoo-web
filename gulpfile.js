//sudo npm install --save-dev gulp gulp-shell yargs gulp-if gulp-uglify gulp-size gulp-less gulp-rename gulp-replace gulp-git gulp-s3 gulp-clean

var gulp = require('gulp');
var args   = require('yargs').argv;
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var size = require('gulp-size');
var less = require('gulp-less');
var imagemin = require('gulp-imagemin');
var rename = require("gulp-rename");
var replace = require("gulp-replace");
var git = require("gulp-git");
var s3 = require("gulp-s3");
var clean = require("gulp-clean");
var print = require("gulp-print");
var gulpif = require("gulp-if");
var connect = require("gulp-connect");
var shell = require("gulp-shell");
var rev = require('gulp-rev');

var isPro = args.pro || args.server == "pro";
var isPre = args.pre;
var isDev = !isPro && !isPre;

//TODO: take it from env vars
var dev_url = '/static';
var pre_url = 'http://s3-eu-west-1.amazonaws.com/dareyoo-pre';
var pro_url = 'https://s3-eu-west-1.amazonaws.com/dareyoo-pro';

var paths = {
  html: ['./static/beta/partials/**', './static/beta/partials/directives/**'],
  app_scripts: ['./static/beta/js/ng-time-relative.js',
            './static/beta/js/services.js',
            './static/beta/js/directives.js',
            './static/beta/js/controllers.js',
            './static/beta/js/filters.js',
            './static/beta/js/app.js'],
  app_scripts_libs: ['./static/beta/lib/jquery/jquery.min.js',
                './static/beta/lib/bootstrap/dist/js/bootstrap.min.js',
                './static/beta/lib/angular/angular.min.js',
                './static/beta/lib/angular-route/angular-route.min.js',
                './static/beta/lib/angular-bootstrap/ui-bootstrap-tpls.min.js',
                './static/beta/lib/angular-ui-router/release/angular-ui-router.min.js',
                './static/beta/lib/angular-cookies/angular-cookies.min.js',
                './static/beta/lib/angular-facebook/angular-facebook.js',
                './static/beta/lib/momentjs/min/moment-with-langs.min.js',
                './static/beta/lib/retina.js/dist/retina.min.js',
                './static/beta/lib/hello/dist/hello.all.js',
                './static/beta/lib/angular-ui-utils/ui-utils.min.js',
                './static/beta/lib/angular-socialshare/angular-socialshare.min.js'],
  landing_scripts: ['./static/beta/js/landing.js'],
  landing_scripts_libs: ['./static/beta/lib/jquery/jquery.min.js',
                './static/beta/lib/jquery.scrollTo/jquery.scrollTo.min.js',
                './static/beta/lib/jquery.localScroll/jquery.localScroll.min.js',
                './static/beta/lib/jquery.parallax/jquery.parallax.js',
                './static/beta/lib/bootstrap/dist/js/bootstrap.min.js',
                './static/beta/lib/retina.js/dist/retina.min.js',
                './static/beta/lib/magnific-popup/dist/jquery.magnific-popup.min.js',
                './static/beta/lib/hello/dist/hello.all.min.js'],
  app_less: ['./static/beta/less/app.less'],
  landing_less: ['./static/beta/less/landing.less'],
  less_libs: ['./static/beta/less',
              './static/beta/lib/bootstrap/less',
              './static/beta/lib/retina.js/src/retina.less',
              './static/beta/lib/zocial-less/css/zocial.less',
              './static/beta/lib/angular-socialshare/angular-socialshare.less',
              './static/beta/less/common.less',
              './static/beta/less/fonts.less'],
  css_libs: [],
  images: ['./static/beta/img/**'],
  fonts_libs: ['./static/beta/lib/bootstrap/dist/fonts/**',
                './static/beta/lib/zocial-less/css/*webfont*']
};

gulp.task('html', function(){
  return gulp.src(paths.html)
        .pipe(size())
        //.pipe(replace('PATHX', 'foo'))
        .pipe(gulp.dest('./static/beta/build/partials'));
});

gulp.task('copy_scripts', function() {
  // Copy vendor JavaScript
  return gulp.src(paths.app_scripts_libs.concat(paths.app_scripts))
    .pipe(size())
    .pipe(gulp.dest('./static/beta/build/js'));
});

gulp.task('app_all_min_scripts', function() {
  // Unify, minify and copy all JavaScript
  return gulp.src(paths.app_scripts_libs.concat(paths.app_scripts))
    .pipe(uglify())
    .pipe(concat('dareyoo_app.all.min.js'))
    .pipe(gulp.dest('./static/beta/build/js'));
});

gulp.task('app_all_min_scripts_rev', function() {
  return gulp.src(paths.app_scripts_libs.concat(paths.app_scripts))
    .pipe(uglify())
    .pipe(concat('dareyoo_app.all.min.js'))
    .pipe(rev())
    .pipe(print())
    .pipe(size())
    .pipe(gulp.dest('./static/beta/build/js'));
});

gulp.task('landing_all_min_scripts', function() {
  // Unify, minify and copy all JavaScript
  return gulp.src(paths.landing_scripts_libs.concat(paths.landing_scripts))
    .pipe(uglify())
    .pipe(concat('dareyoo_landing.all.min.js'))
    .pipe(gulp.dest('./static/beta/build/js'));
});

gulp.task('landing_all_min_scripts_rev', function() {
  // Unify, minify and copy all JavaScript
  return gulp.src(paths.landing_scripts_libs.concat(paths.landing_scripts))
    .pipe(uglify())
    .pipe(concat('dareyoo_landing.all.min.js'))
    .pipe(rev())
    .pipe(print())
    .pipe(size())
    .pipe(gulp.dest('./static/beta/build/js'));
});

// All scripts
gulp.task('scripts', ['copy_scripts', 'app_all_min_scripts', 'landing_all_min_scripts']);
gulp.task('scripts_rev', ['copy_scripts', 'app_all_min_scripts_rev', 'landing_all_min_scripts_rev']);

gulp.task('app_less', function () {
  var less_base_url = dev_url;
  if(isPre) less_base_url = pre_url;
  if(isPro) less_base_url = pro_url;
  return gulp.src(paths.app_less)
        .pipe(replace("[[LESS_BASE_URL]]", less_base_url))
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('dareyoo_app.all.min.css'))
        .pipe(gulp.dest('./static/beta/build/css'));
});
gulp.task('app_less_rev', function () {
  var less_base_url = dev_url;
  if(isPre) less_base_url = pre_url;
  if(isPro) less_base_url = pro_url;
  return gulp.src(paths.app_less)
        .pipe(replace("[[LESS_BASE_URL]]", less_base_url))
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('dareyoo_app.all.min.css'))
        .pipe(rev())
        .pipe(print())
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/css'));
});

gulp.task('landing_less', function () {
  var less_base_url = dev_url;
  if(isPre) less_base_url = pre_url;
  if(isPro) less_base_url = pro_url;
  return gulp.src(paths.landing_less)
        .pipe(replace("[[LESS_BASE_URL]]", less_base_url))
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('landing.all.min.css'))
        .pipe(gulp.dest('./static/beta/build/css'));
});

gulp.task('landing_less_rev', function () {
  var less_base_url = dev_url;
  if(isPre) less_base_url = pre_url;
  if(isPro) less_base_url = pro_url;
  return gulp.src(paths.landing_less)
        .pipe(replace("[[LESS_BASE_URL]]", less_base_url))
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('landing.all.min.css'))
        .pipe(rev())
        .pipe(print())
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/css'));
});

gulp.task('vendor_css', function () {
  /* return gulp.src(paths.css_libs)
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/css'));*/
});

// All css
gulp.task('css', ['app_less', 'landing_less']);
gulp.task('css_rev', ['app_less_rev', 'landing_less_rev']);

gulp.task('fonts', function () {
  return gulp.src(paths.fonts_libs)
        .pipe(size())
        .pipe(gulp.dest('./static/beta/build/fonts'));
});

//Replace paths in templates/css/js depending on production/developement
gulp.task('paths', function () {
  console.log("Hola!" + args.jeje + args.jaja);
});

gulp.task('images', function () {
  return gulp.src(paths.images)
        .pipe(imagemin())
        .pipe(gulp.dest('./static/beta/build/img'));
});

// Rerun the task when a file changes
gulp.task('watch', ['build_dev'], function() {
  gulp.watch(paths.html, ['html']);
  gulp.watch(paths.app_scripts, ['scripts']);
  gulp.watch(paths.landing_scripts, ['scripts']);
  gulp.watch(paths.landing_less.concat(paths.less_libs), ['css']);
  gulp.watch(paths.app_less.concat(paths.less_libs), ['css']);
  gulp.watch(paths.images, ['images']);
});

// Deploy to S3. TODO (this code is just an example)
gulp.task('s3', function() {
  aws = JSON.parse(fs.readFileSync('./aws.json'));
  options = { delay: 1000 } // optional delay each request by x milliseconds
  gulp.src('./dist/**', {read: false})
      .pipe(s3(aws, options));
});

gulp.task('deploy', function(done){
  //var options = {args: " -f"};
  var options = {};
  var branch = "master";
  console.log('Branch: ' + JSON.stringify(process.stdout, null, 4) + '.');
  //git.push('pro', 'master', options, done);
});

gulp.task('clean', function () {
    return gulp.src(['build/css', 'build/js', 'build/img', 'build/partials'], {read: false}).pipe(clean());
});

gulp.task('env', function () {
    console.log('Env ' + process.env.PROJECT_NAME);
    process.env.PROJECT_NAME = isPro;
    console.log('Env ' + process.env.PROJECT_NAME);
    return gulp.src('.')
        .pipe(gulpif(isPro == "lala", shell('echo $PROJECT_NAME')))
        .pipe(gulpif(!isPro, shell('pwd')))
});

// Build
gulp.task('build', ['html', 'css_rev', 'scripts_rev', 'fonts']);
gulp.task('build_dev', ['html', 'css', 'scripts', 'fonts']);

// Default task (called when you run `gulp` from cli)
gulp.task('default', function () {
    gulp.start('watch');
});