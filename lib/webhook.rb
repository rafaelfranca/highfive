require 'rack/request'

class Webhook
  def call(env)
    req = Rack::Request.new(env)

    if req.get_header('HTTP_X_GITHUB_EVENT') == 'pull_request'
      [204, {}, [""]]
    else
      [200, {}, ["OK"]]
    end
  end
end
