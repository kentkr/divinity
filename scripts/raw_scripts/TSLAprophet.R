library(data.table)
library(tidyverse)
library(prophet)

setwd('~/Dropbox/algo_alpaca')

tsla <- as.data.table(read.csv('data/raw_data/TSLAdaily_yf.csv'))

dt <- tsla[,.(timestamp, close)]
names(dt) <- c('ds', 'y')
dt$ds <- as.POSIXct(dt$ds)

m <- prophet(dt[ds > '2020-12-31'])

future <- make_future_dataframe(m, periods = 1)

forecast <- predict(m, future)

plot(m, forecast)

