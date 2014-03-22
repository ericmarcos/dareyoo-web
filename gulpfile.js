var gulp = require('gulp');
var less = require('gulp-less');
var path = require('path');
var rename = require("gulp-rename");

var paths = {
  scripts: ['.static/beta/js/*.js'],
  less: './static/beta/less/dareyoo.less',
  less_libs: ['./static/beta/less', './static/beta/lib/bootstrap/less']
};

gulp.task('scripts', function() {
  // Minify and copy all JavaScript (except vendor scripts)
  return gulp.src(paths.scripts)
    .pipe(uglify())
    .pipe(concat('dareyoo.min.js'))
    .pipe(size())
    .pipe(gulp.dest('./static/beta/js'));
});

gulp.task('less', function () {
  return gulp.src(paths.less)
        .pipe(less({
            compress: true,
            paths: paths.less_libs
        }))
        .pipe(rename('dareyoo.min.css'))
        .pipe(gulp.dest('./static/beta/css'));
});

// Rerun the task when a file changes
gulp.task('watch', function() {
  gulp.watch(paths.less, ['less']);
});

// The default task (called when you run `gulp` from cli)
gulp.task('default', ['less', 'watch']);