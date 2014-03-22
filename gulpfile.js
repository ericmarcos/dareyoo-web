var gulp = require('gulp');
var less = require('gulp-less');
var path = require('path');

var paths = {
  scripts: '.static/beta/js/**/*.js',
  less: './static/beta/less/*.less'
};

gulp.task('less', function () {
  gulp.src(paths.less)
    .pipe(less({
      paths: [ path.join(__dirname, 'less', 'includes') ]
    }))
    .pipe(gulp.dest('./static/beta/css'));
});

// Rerun the task when a file changes
gulp.task('watch', function() {
  gulp.watch(paths.less, ['less']);
});

// The default task (called when you run `gulp` from cli)
gulp.task('default', ['less', 'watch']);