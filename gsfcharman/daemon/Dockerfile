FROM python:3.14-slim AS build_ruby

# Install ruby-build dependencies
RUN apt update && apt install -y build-essential autoconf curl git libssl-dev libyaml-dev zlib1g-dev libffi-dev libgmp-dev rustc

# This is somewhat unnecessary as we could just run ruby-build directly, but I went off the Lich wiki instructions so here we are
ENV RBENV_ROOT /usr/local/rbenv
RUN git clone https://github.com/rbenv/rbenv.git $RBENV_ROOT && \
    mkdir -p $RBENV_ROOT/plugins && \
    git clone https://github.com/rbenv/ruby-build.git $RBENV_ROOT/plugins/ruby-build

# Set up rbenv in the shell
ENV PATH="$RBENV_ROOT/bin:$RBENV_ROOT/shims:$PATH"
RUN echo 'eval "$(rbenv init -)"' >> ~/.bashrc

# Install ruby
RUN rbenv install 4.0.1 && \
    rbenv global 4.0.1 && \
    rbenv rehash

# Used by the daemon to find the desired ruby version, this is the output of `rbenv which ruby`
ENV RUBY_BIN /usr/local/rbenv/versions/4.0.1/bin/ruby

FROM build_ruby AS build_lich

# Install lich dependencies
RUN apt install -y libcairo2-dev libgdk-pixbuf-2.0-dev libgirepository1.0-dev unzip

# Install lich 5
WORKDIR /opt
RUN curl -L "https://github.com/elanthia-online/lich-5/releases/latest/download/lich-5.zip" -o temp.zip && unzip temp.zip -d ./ && rm temp.zip

# Install lich ruby dependencies
RUN gem install bundler --no-document
RUN cd Lich5 && bundle install

# Used by the daemon to find lich
ENV LICH_PATH /opt/Lich5
ENV LICH_BIN "$LICH_PATH/lich.rbw"

FROM build_lich AS build_app

WORKDIR /opt/gsfcharman
COPY --chown=charman:charman . .
RUN pip install -r requirements.txt
WORKDIR /opt
CMD ["python", "-u", "-m", "gsfcharman.daemon.main"]