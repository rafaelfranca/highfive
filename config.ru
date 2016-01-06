$LOAD_PATH.unshift('lib')

require 'rails-bot'

run Webhook.new(Bot.new)
