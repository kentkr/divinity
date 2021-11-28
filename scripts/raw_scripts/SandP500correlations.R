
# libs and wd

setwd('~/Dropbox/algo_alpaca')

library(data.table)
library(tidyverse)

# load data
spDays = as.data.table(read.csv('data/raw_data/spDays3monthsFrom073121.csv'))

spDays$timestamp <- as.POSIXct(spDays$timestamp)

# make wider
spDays[, .N, symbol]
spDays[, length(unique(close)), symbol]
close <- as.data.table(pivot_wider(spDays, 
                                   id_cols = timestamp,
                                   names_from = symbol,
                                   values_from = close))
