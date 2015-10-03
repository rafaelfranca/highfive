require 'rack/request'
require 'json'

class Webhook
  def call(env)
    req = Rack::Request.new(env)

    if req.get_header('HTTP_X_GITHUB_EVENT') == 'pull_request'
      payload = JSON.parse(req.get_header('rack.input').read)

      if payload['action'] == 'opened'
        [201, {}, [""]]
      else
        default_response
      end
    else
      default_response
    end
  end

  private

  def default_response
    [200, {}, ["OK"]]
  end
end
