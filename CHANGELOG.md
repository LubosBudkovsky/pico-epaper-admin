## 0.2.1
- Improved weather info alignment for `Weather with Quote` template
- Context variable injection into layout is now performed in the refresh step; renderer receives a pre-resolved layout

## 0.2.0
- Added `Weather with Quote` template
- Added `invert_colors` setting — display dark background with light content
- Reduced memory usage during screen refresh to prevent out-of-memory crashes
- Context provider HTTP requests now retry on failure
- NTP time sync on boot now retries on failure

## 0.1.0
- Initial release